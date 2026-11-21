"""Command-line preview: python main.py [COT_NAME]  (default: EURO FX)."""

import sys

from charts import apply_shared_crosshair, build_stacked_chart
from data_processor import load_and_align_data
from symbols import COT_TO_MT5


def main(cot_name: str = "EURO FX", num_bars: int = 1000) -> int:
    cot_name = cot_name.upper()
    if cot_name not in COT_TO_MT5:
        print(f"Unknown COT market '{cot_name}'. Choose one of: {', '.join(COT_TO_MT5)}")
        return 2

    pair = COT_TO_MT5[cot_name]
    result = load_and_align_data(pair, cot_name, num_bars)
    if result.error:
        print(result.error)
        return 1

    apply_shared_crosshair(build_stacked_chart(result.merged, pair, cot_name)).show()
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
