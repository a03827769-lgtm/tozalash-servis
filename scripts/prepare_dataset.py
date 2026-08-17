import asyncio
import json
import os
import sys
from pathlib import Path

# Loyiha papkasini Python path'ga qo'shish
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import db


async def export_dataset():
    """AI Fine-tuning uchun ai_learning va conversations jadvallaridan dataset yig'ish"""
    await db.init_db()

    dataset = []

    async with db.get_conn() as conn:
        async with conn.cursor() as cursor:
            # ai_learning jadvalidan successful patternlarni olish
            await cursor.execute(
                "SELECT input_data, output_data FROM ai_learning WHERE success = 1"
            )
            rows = await cursor.fetchall()

            for row in rows:
                # ChatML yoki ShareGPT format (soddalashtirilgan instruction format)
                dataset.append(
                    {"instruction": row["input_data"], "output": row["output_data"]}
                )

    output_file = Path(__file__).parent.parent / "data" / "dataset.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Dataset muvaffaqiyatli yaratildi. Jami qatorlar: {len(dataset)}")
    print(f"Manzil: {output_file}")


if __name__ == "__main__":
    asyncio.run(export_dataset())
