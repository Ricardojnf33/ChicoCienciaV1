from pathlib import Path
import matplotlib.pyplot as plt
import json

class PlotTool:
    name = "plot_tool"

    def save_lineplot(self, xs, ys, title: str, out_path: str):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        plt.figure()
        plt.plot(xs, ys)
        plt.title(title)
        plt.xlabel("x")
        plt.ylabel("y")
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        meta = {"title": title, "path": out_path}
        Path(out_path + ".json").write_text(json.dumps(meta, indent=2))
        return meta
