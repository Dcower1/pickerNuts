from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict
import requests
from db.nuts_db import get_connection


@dataclass
class ClassificationSession:
    classification_id: int
    supplier_id: int
    started_at: str
    counts: Dict[str, int] = field(default_factory=lambda: {"A": 0, "B": 0, "C": 0, "D": 0})
    total_nuts: int = 0
    active: bool = True

    def registrar_detalle(self, categoria: str, shape: str) -> None:
        if not self.active or categoria not in self.counts:
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO classification_details (classification_id, grade, shape)
                VALUES (?, ?, ?)
                """,
                (self.classification_id, categoria, shape),
            )
            cursor.execute(
                "UPDATE classifications SET total_nuts = total_nuts + 1 WHERE classification_id = ?",
                (self.classification_id,),
            )
            cursor.execute(
                "SELECT total_nuts FROM classifications WHERE classification_id = ?",
                (self.classification_id,),
            )
            row = cursor.fetchone()
            if row:
                self.total_nuts = int(row[0])
            else:
                self.total_nuts += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        self.counts[categoria] += 1


    #ESTO es lo que hace el proceso de enviar al N8N
    def finalizar(self) -> None:
        if not self.active:
            return

        total_detectado = sum(self.counts.values())
        total = max(self.total_nuts, total_detectado)

        if total <= 0:
            self._eliminar_sesion_vacia()
            self.total_nuts = 0
            self.active = False
            return

        self.total_nuts = total

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Actualizar total en la tabla classifications
            cursor.execute(
                "UPDATE classifications SET total_nuts = ? WHERE classification_id = ?",
                (self.total_nuts, self.classification_id),
            )

            # Insertar en el historial
            cursor.execute(
                """
                INSERT INTO metrics_history (
                    classification_id, supplier_id, date, total_nuts,
                    count_A, count_B, count_C, count_D
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.classification_id,
                    self.supplier_id,
                    self.started_at,
                    self.total_nuts,
                    self.counts.get("A", 0),
                    self.counts.get("B", 0),
                    self.counts.get("C", 0),
                    self.counts.get("D", 0),
                ),
            )

            # Obtener nombre del proveedor
            cursor.execute(
                "SELECT name FROM suppliers WHERE supplier_id = ?",
                (self.supplier_id,)
            )
            supplier_name_row = cursor.fetchone()
            supplier_name = supplier_name_row[0] if supplier_name_row else f"Proveedor #{self.supplier_id}"

            conn.commit()

            # Enviar datos a n8n (con nombre incluido)
            try:
                payload = {
                    "classification_id": self.classification_id,
                    "supplier_name": supplier_name,  # 👈 Ahora enviamos el nombre
                    "supplier_id": self.supplier_id,
                    "total_nuts": self.total_nuts,
                    "counts": self.counts,
                }

                requests.post(
                    "https://diegorojas1.app.n8n.cloud/webhook-test/clasificacion-finalizada",
                    json=payload,
                    timeout=5
                )
                print(f"📨 Datos enviados correctamente a n8n ✅ ({supplier_name})")

            except Exception as e:
                print(f"[WARN] No se pudo notificar a n8n: {e}")

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        self.active = False


    def _eliminar_sesion_vacia(self) -> None:
        """Elimina la clasificación creada si nunca se detectaron nueces."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM classifications WHERE classification_id = ?",
                (self.classification_id,),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class ClassificationSessionDAO:
    @staticmethod
    def iniciar_sesion(supplier_id: int) -> ClassificationSession:
        started_at = datetime.utcnow().isoformat(timespec="seconds")
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO classifications (supplier_id, date, total_nuts)
                VALUES (?, ?, 0)
                """,
                (supplier_id, started_at),
            )
            classification_id = cursor.lastrowid
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ClassificationSession(
            classification_id=classification_id,
            supplier_id=supplier_id,
            started_at=started_at,
        )

    @staticmethod
    def obtener_totales_proveedor(supplier_id: int) -> tuple[Dict[str, int], int]:
        counts = {"A": 0, "B": 0, "C": 0, "D": 0}
        total = 0
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT cd.grade, COUNT(*)
                FROM classification_details cd
                JOIN classifications c ON cd.classification_id = c.classification_id
                WHERE c.supplier_id = ?
                GROUP BY cd.grade
                """,
                (supplier_id,),
            )
            for grade, cantidad in cursor.fetchall():
                if not grade:
                    continue
                clave = str(grade).strip().upper()
                if clave in counts:
                    counts[clave] = int(cantidad)
            total = sum(counts.values())
        finally:
            conn.close()
        return counts, total

    @staticmethod
    def obtener_historial_metrics(
        supplier_id: int,
        page: int = 1,
        page_size: int = 6,
    ) -> dict:
        """Obtiene el historial de métricas almacenado para un proveedor."""
        if page_size <= 0:
            page_size = 6
        page = max(page, 1)
        total_rows = 0
        total_pages = 1
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM metrics_history WHERE supplier_id = ?",
                (supplier_id,),
            )
            total_rows = int(cursor.fetchone()[0] or 0)
            if total_rows > 0:
                total_pages = max((total_rows + page_size - 1) // page_size, 1)
                page = min(page, total_pages)
                offset = (page - 1) * page_size
            else:
                page = 1
                offset = 0

            cursor.execute(
                """
                SELECT date, total_nuts, count_A, count_B, count_C, count_D, avg_size
                FROM metrics_history
                WHERE supplier_id = ?
                ORDER BY date DESC
                LIMIT ? OFFSET ?
                """,
                (supplier_id, page_size, offset),
            )
            rows = [
                {
                    "date": row[0],
                    "total_nuts": row[1],
                    "count_A": row[2],
                    "count_B": row[3],
                    "count_C": row[4],
                    "count_D": row[5],
                    "avg_size": row[6],
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

        return {
            "rows": rows,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_rows": total_rows,
        }
