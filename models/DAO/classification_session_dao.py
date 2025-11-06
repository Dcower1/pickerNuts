from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

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

    def finalizar(self) -> None:
        if not self.active:
            return

        total = sum(self.counts.values())
        self.total_nuts = max(self.total_nuts, total)

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE classifications SET total_nuts = ? WHERE classification_id = ?",
                (self.total_nuts, self.classification_id),
            )
            cursor.execute(
                """
                INSERT INTO metrics_history (
                    classification_id,
                    supplier_id,
                    date,
                    total_nuts,
                    count_A,
                    count_B,
                    count_C,
                    count_D
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
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        self.active = False


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
