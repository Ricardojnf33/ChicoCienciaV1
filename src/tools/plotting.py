from pathlib import Path
import json

class PlotTool:
    name = "plot_tool"

    def save_lineplot(self, xs, ys, title: str, out_path: str):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            import matplotlib.pyplot as plt  # lazy import
            plt.figure()
            plt.plot(xs, ys)
            plt.title(title)
            plt.xlabel("x")
            plt.ylabel("y")
            plt.tight_layout()
            plt.savefig(out_path)
            plt.close()
            generated = True
        except Exception:
            # Fallback sem matplotlib: não gera imagem, apenas metadata
            generated = False
        meta = {"title": title, "path": out_path, "generated": generated}
        Path(out_path + ".json").write_text(json.dumps(meta, indent=2))
        return meta
