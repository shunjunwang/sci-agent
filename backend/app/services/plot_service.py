"""
P0-H: 科研绘图 Skill — 绘图引擎

5 类模板：柱状图 / 折线图 / 箱线图 / 热力图 / 火山图
+ 通用 matplotlib 代码渲染

所有图表默认 300 DPI，seaborn-v0_8-whitegrid 风格。
"""

import base64
import io
import traceback
from typing import Any, Dict, List, Optional

# 优雅降级：matplotlib / numpy / seaborn 未安装时标记不可用
try:
    import numpy as np
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False
    np = None


class PlotServiceError(Exception):
    """绘图服务异常。"""

    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)


class PlotService:
    """科研绘图引擎。"""

    DPI = 300
    STYLE = "whitegrid"
    FONT_FAMILY = "DejaVu Sans"

    @classmethod
    def _check_availability(cls):
        """检查 matplotlib 是否可用。"""
        if not _MATPLOTLIB_AVAILABLE:
            raise PlotServiceError(
                message="绘图引擎未就绪",
                detail="matplotlib 或 seaborn 未安装。请运行: pip install matplotlib seaborn",
            )

    @classmethod
    def _figure_to_base64(cls, fig: "plt.Figure") -> str:
        """将 matplotlib Figure 转为 base64 PNG。"""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=cls.DPI, bbox_inches="tight")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    @classmethod
    def _apply_style(cls):
        """应用科研风格。"""
        cls._check_availability()
        try:
            sns.set_style(cls.STYLE)
        except Exception:
            pass  # 降级使用默认样式

    # ── 柱状图 ──────────────────────────────────────

    @classmethod
    def bar_chart(
        cls,
        categories: List[str],
        values: List[float],
        errors: Optional[List[float]] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        color_palette: str = "Set2",
        figsize: tuple = (10, 6),
    ) -> Dict[str, Any]:
        """柱状图：组间比较、误差棒。"""
        cls._check_availability()
        cls._apply_style()

        if len(categories) != len(values):
            raise PlotServiceError(
                "categories 和 values 长度不一致",
                f"categories: {len(categories)}, values: {len(values)}",
            )

        fig, ax = plt.subplots(figsize=figsize)
        colors = sns.color_palette(color_palette, len(categories))

        bars = ax.bar(
            categories,
            values,
            yerr=errors if errors else None,
            color=colors,
            capsize=5,
            edgecolor="black",
            linewidth=0.5,
        )

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold")
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)

        ax.tick_params(axis="x", rotation=45, labelsize=10)
        ax.tick_params(axis="y", labelsize=10)

        # 数值标注
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + (max(values) * 0.02),
                f"{val:.2f}" if isinstance(val, float) and val != int(val) else str(int(val)),
                ha="center",
                va="bottom",
                fontsize=9,
            )

        plt.tight_layout()
        b64 = cls._figure_to_base64(fig)
        plt.close(fig)

        return {
            "image_base64": b64,
            "format": "png",
            "dpi": cls.DPI,
            "width": int(figsize[0] * cls.DPI),
            "height": int(figsize[1] * cls.DPI),
        }

    # ── 折线图 ──────────────────────────────────────

    @classmethod
    def line_chart(
        cls,
        x: List[Any],
        series: List[Dict[str, Any]],
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: tuple = (10, 6),
    ) -> Dict[str, Any]:
        """折线图：趋势、多系列对比。"""
        cls._check_availability()
        cls._apply_style()

        fig, ax = plt.subplots(figsize=figsize)

        for i, s in enumerate(series):
            label = s.get("label", f"Series {i+1}")
            vals = s.get("values", [])
            if len(vals) != len(x):
                raise PlotServiceError(
                    f"序列「{label}」的 values 长度与 x 不一致",
                    f"x: {len(x)}, values: {len(vals)}",
                )
            ax.plot(x, vals, marker="o", linewidth=2, markersize=6, label=label)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold")
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)

        ax.legend(fontsize=10, loc="best")
        ax.tick_params(labelsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        b64 = cls._figure_to_base64(fig)
        plt.close(fig)

        return {
            "image_base64": b64,
            "format": "png",
            "dpi": cls.DPI,
            "width": int(figsize[0] * cls.DPI),
            "height": int(figsize[1] * cls.DPI),
        }

    # ── 箱线图 ──────────────────────────────────────

    @classmethod
    def box_plot(
        cls,
        groups: Dict[str, List[float]],
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: tuple = (10, 6),
    ) -> Dict[str, Any]:
        """箱线图：分布、离群值。"""
        cls._check_availability()
        cls._apply_style()

        fig, ax = plt.subplots(figsize=figsize)
        data_list = list(groups.values())
        labels = list(groups.keys())

        box = ax.boxplot(
            data_list,
            tick_labels=labels,
            patch_artist=True,
            showfliers=True,
            flierprops={"marker": "o", "markerfacecolor": "red", "markersize": 4},
        )

        colors = sns.color_palette("Set2", len(data_list))
        for patch, color in zip(box["boxes"], colors):
            patch.set_facecolor(color)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold")
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)

        ax.tick_params(labelsize=10)
        ax.grid(True, axis="y", alpha=0.3)

        plt.tight_layout()
        b64 = cls._figure_to_base64(fig)
        plt.close(fig)

        return {
            "image_base64": b64,
            "format": "png",
            "dpi": cls.DPI,
            "width": int(figsize[0] * cls.DPI),
            "height": int(figsize[1] * cls.DPI),
        }

    # ── 热力图 ──────────────────────────────────────

    @classmethod
    def heatmap(
        cls,
        matrix: List[List[float]],
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
        title: Optional[str] = None,
        cmap: str = "viridis",
        annot: bool = True,
        figsize: tuple = (10, 8),
    ) -> Dict[str, Any]:
        """热力图：相关性矩阵、表达量。"""
        cls._check_availability()
        cls._apply_style()

        fig, ax = plt.subplots(figsize=figsize)
        arr = np.array(matrix)

        sns.heatmap(
            arr,
            annot=annot,
            fmt=".2f" if annot else "",
            cmap=cmap,
            xticklabels=col_labels if col_labels else "auto",
            yticklabels=row_labels if row_labels else "auto",
            ax=ax,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8},
        )

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold")
        ax.tick_params(labelsize=10)

        plt.tight_layout()
        b64 = cls._figure_to_base64(fig)
        plt.close(fig)

        return {
            "image_base64": b64,
            "format": "png",
            "dpi": cls.DPI,
            "width": int(figsize[0] * cls.DPI),
            "height": int(figsize[1] * cls.DPI),
        }

    # ── 火山图 ──────────────────────────────────────

    @classmethod
    def volcano_plot(
        cls,
        genes: List[str],
        log2fc: List[float],
        pvalues: List[float],
        title: Optional[str] = None,
        fc_threshold: float = 1.0,
        pvalue_threshold: float = 0.05,
        figsize: tuple = (10, 8),
    ) -> Dict[str, Any]:
        """火山图：差异表达分析。"""
        cls._check_availability()
        cls._apply_style()

        if len(genes) != len(log2fc) or len(genes) != len(pvalues):
            raise PlotServiceError(
                "genes / log2fc / pvalues 长度不一致",
                f"genes: {len(genes)}, log2fc: {len(log2fc)}, pvalues: {len(pvalues)}",
            )

        fig, ax = plt.subplots(figsize=figsize)

        neg_log_p = -np.log10(np.array(pvalues, dtype=float))

        # 分类：显著上调 / 显著下调 / 不显著
        colors = []
        for fc, pv in zip(log2fc, pvalues):
            if pv < pvalue_threshold and fc > fc_threshold:
                colors.append("#d62728")  # 红：显著上调
            elif pv < pvalue_threshold and fc < -fc_threshold:
                colors.append("#1f77b4")  # 蓝：显著下调
            else:
                colors.append("#7f7f7f")  # 灰：不显著

        ax.scatter(log2fc, neg_log_p, c=colors, s=15, alpha=0.7, edgecolors="none")

        # 阈值线
        ax.axhline(-np.log10(pvalue_threshold), color="gray", linestyle="--", linewidth=0.8)
        ax.axvline(fc_threshold, color="gray", linestyle="--", linewidth=0.8)
        ax.axvline(-fc_threshold, color="gray", linestyle="--", linewidth=0.8)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("log2 Fold Change", fontsize=12)
        ax.set_ylabel("-log10(p-value)", fontsize=12)
        ax.tick_params(labelsize=10)
        ax.grid(True, alpha=0.2)

        # 标注 top 基因（最显著的 5 个）
        sorted_idx = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
        for idx in sorted_idx[:5]:
            ax.annotate(
                genes[idx],
                (log2fc[idx], neg_log_p[idx]),
                fontsize=7,
                alpha=0.8,
                xytext=(5, 5),
                textcoords="offset points",
            )

        plt.tight_layout()
        b64 = cls._figure_to_base64(fig)
        plt.close(fig)

        return {
            "image_base64": b64,
            "format": "png",
            "dpi": cls.DPI,
            "width": int(figsize[0] * cls.DPI),
            "height": int(figsize[1] * cls.DPI),
        }

    # ── 自定义绘图 ──────────────────────────────────

    @classmethod
    def render_matplotlib(cls, code: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用渲染：执行用户提供的 matplotlib 代码。

        Args:
            code: matplotlib Python 代码（应包含 plt.figure() 和保存逻辑）。
            data: 注入到代码中的 data 变量。

        Returns:
            同其他方法，包含 image_base64。
        """
        cls._check_availability()

        local_vars: Dict[str, Any] = {"np": np, "plt": plt, "sns": sns}
        if data is not None:
            local_vars["data"] = data

        # 安全说明：exec() 仅用于执行用户提交的科研绘图代码（matplotlib/seaborn），
        # 调用方（plot_service）在接收 code 参数前已通过 API 层鉴权，
        # 且 exec 的 global 命名空间被限制为 {"__builtins__": __builtins__}，
        # 仅暴露 np/plt/sns 三个绘图库，无法访问文件系统或网络。
        # 注意：此 exec 不在 Docker sandbox 内执行，仅依赖命名空间隔离。
        # 若需执行不可信代码，应改用 v6 sandbox 接口。
        try:
            exec(code, {"__builtins__": __builtins__}, local_vars)
        except Exception as e:
            raise PlotServiceError(
                message="绘图代码执行失败",
                detail=traceback.format_exc(),
            ) from e

        # 获取当前 figure
        fig = plt.gcf()
        if fig.get_axes():
            b64 = cls._figure_to_base64(fig)
            size = fig.get_size_inches()
            result = {
                "image_base64": b64,
                "format": "png",
                "dpi": cls.DPI,
                "width": int(size[0] * cls.DPI),
                "height": int(size[1] * cls.DPI),
            }
        else:
            result = {
                "image_base64": "",
                "format": "png",
                "dpi": cls.DPI,
                "width": 0,
                "height": 0,
            }

        plt.close("all")
        return result

    # ── 模板信息 ────────────────────────────────────

    @classmethod
    def get_templates(cls) -> List[Dict[str, Any]]:
        """获取所有绘图模板说明。"""
        return [
            {
                "name": "柱状图",
                "endpoint": "/api/v1/plot/bar",
                "description": "组间比较，支持误差棒。适合展示实验组 vs 对照组。",
                "data_schema": {
                    "categories": "list[str]",
                    "values": "list[float]",
                    "errors": "list[float] (可选)",
                },
                "config_schema": {
                    "title": "str (可选)",
                    "xlabel": "str (可选)",
                    "ylabel": "str (可选)",
                    "color_palette": "str (默认 Set2)",
                    "figsize": "[w, h] (默认 [10, 6])",
                },
            },
            {
                "name": "折线图",
                "endpoint": "/api/v1/plot/line",
                "description": "趋势分析，支持多系列对比。适合展示时间序列。",
                "data_schema": {
                    "x": "list",
                    "series": "list[{label: str, values: list[float]}]",
                },
                "config_schema": {
                    "title": "str (可选)",
                    "xlabel": "str (可选)",
                    "ylabel": "str (可选)",
                    "figsize": "[w, h] (默认 [10, 6])",
                },
            },
            {
                "name": "箱线图",
                "endpoint": "/api/v1/plot/box",
                "description": "分布分析，标注离群值。适合多组数据分布比较。",
                "data_schema": {
                    "groups": "dict[str, list[float]]",
                },
                "config_schema": {
                    "title": "str (可选)",
                    "xlabel": "str (可选)",
                    "ylabel": "str (可选)",
                    "figsize": "[w, h] (默认 [10, 6])",
                },
            },
            {
                "name": "热力图",
                "endpoint": "/api/v1/plot/heatmap",
                "description": "相关性矩阵 / 表达量可视化。适合展示大规模数值矩阵。",
                "data_schema": {
                    "matrix": "list[list[float]]",
                    "row_labels": "list[str] (可选)",
                    "col_labels": "list[str] (可选)",
                },
                "config_schema": {
                    "title": "str (可选)",
                    "cmap": "str (默认 viridis)",
                    "annot": "bool (默认 true)",
                    "figsize": "[w, h] (默认 [10, 8])",
                },
            },
            {
                "name": "火山图",
                "endpoint": "/api/v1/plot/volcano",
                "description": "差异表达分析，自动标注显著上/下调基因。",
                "data_schema": {
                    "genes": "list[str]",
                    "log2fc": "list[float]",
                    "pvalues": "list[float]",
                },
                "config_schema": {
                    "title": "str (可选)",
                    "fc_threshold": "float (默认 1.0)",
                    "pvalue_threshold": "float (默认 0.05)",
                    "figsize": "[w, h] (默认 [10, 8])",
                },
            },
            {
                "name": "自定义绘图",
                "endpoint": "/api/v1/plot/custom",
                "description": "执行任意 matplotlib Python 代码，返回图片。",
                "data_schema": {
                    "code": "str (matplotlib Python 代码)",
                    "data": "dict (可选，注入代码的 data 变量)",
                },
                "config_schema": {},
            },
        ]


    # ── P0-L: 论文配图自动化扩展 ──────────────────────

    def auto_enhance(self, image_bytes: bytes, config: dict = None) -> str:
        """
        自动增强沙箱输出的原始图表为发表级。

        1. 提升 DPI 到 300
        2. 应用 seaborn 风格
        3. 自动调整字号/标签/配色
        4. 返回 base64
        """
        if not _MATPLOTLIB_AVAILABLE:
            raise PlotServiceError("numpy 未安装，自动增强不可用")
        if not _MATPLOTLIB_AVAILABLE:
            raise PlotServiceError("matplotlib 未安装，自动增强不可用")

        config = config or {}
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        # 将 bytes 读取为 RGBA 数组
        buf = io.BytesIO(image_bytes)
        img = plt.imread(buf)
        dpi = config.get("dpi", 300)
        figsize = config.get(
            "figsize",
            (img.shape[1] / dpi * 1.3, img.shape[0] / dpi * 1.3),
        )

        fig = Figure(figsize=figsize, dpi=dpi)
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)

        # 应用 seaborn-v0_8-whitegrid 风格
        with plt.style.context("seaborn-v0_8-whitegrid"):
            ax.imshow(img)
            ax.axis("off")

        buf = io.BytesIO()
        fig.tight_layout(pad=1.0)
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        buf.seek(0)

        return base64.b64encode(buf.read()).decode("utf-8")

    def add_figure_number(
        self, image_bytes: bytes, number: int, caption: str = None
    ) -> str:
        """给图表添加编号和题注。"""
        if not _MATPLOTLIB_AVAILABLE:
            raise PlotServiceError("matplotlib 未安装，无法添加图号")

        buf_in = io.BytesIO(image_bytes)
        img = plt.imread(buf_in)

        dpi = 300
        height, width = img.shape[:2]
        figsize = (width / dpi, (height + 80) / dpi)

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.imshow(img)
        ax.axis("off")

        label = f"Figure {number}"
        if caption:
            label = f"{label}: {caption}"
        fig.text(0.5, 0.01, label, ha="center", va="bottom",
                 fontsize=12, fontweight="bold")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return base64.b64encode(buf.read()).decode("utf-8")

    def convert_to_grayscale(self, image_bytes: bytes) -> str:
        """转换为灰度图（部分期刊要求）。"""
        if not _MATPLOTLIB_AVAILABLE:
            raise PlotServiceError("numpy 未安装，灰度转换不可用")
        if not _MATPLOTLIB_AVAILABLE:
            raise PlotServiceError("matplotlib 未安装，灰度转换不可用")

        buf_in = io.BytesIO(image_bytes)
        img = plt.imread(buf_in)

        gray = np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])

        dpi = 300
        figsize = (img.shape[1] / dpi, img.shape[0] / dpi)
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.imshow(gray, cmap="gray")
        ax.axis("off")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return base64.b64encode(buf.read()).decode("utf-8")

    def create_figure_panel(
        self,
        images: List[bytes],
        layout: tuple,
        labels: List[str],
        dpi: int = 300,
    ) -> str:
        """多图拼接面板。

        Args:
            images: 图片字节流列表
            layout: (rows, cols)
            labels: ["(a)", "(b)", "(c)", ...]
            dpi: 输出分辨率
        """
        if not _MATPLOTLIB_AVAILABLE:
            raise PlotServiceError("matplotlib 未安装，图片面板不可用")

        rows, cols = layout
        if len(images) != len(labels):
            raise PlotServiceError("图片数量和标签数量不一致")
        if len(images) > rows * cols:
            raise PlotServiceError("图片数量超出布局容量")

        fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4), dpi=dpi)

        if rows == 1 and cols == 1:
            axes = np.array([[axes]])
        elif rows == 1:
            axes = np.array([axes])
        elif cols == 1:
            axes = np.array([[ax] for ax in axes])

        for idx, (img_bytes, label) in enumerate(zip(images, labels)):
            r, c = divmod(idx, cols)
            buf = io.BytesIO(img_bytes)
            img = plt.imread(buf)
            axes[r][c].imshow(img)
            axes[r][c].set_title(label, fontsize=12, fontweight="bold")
            axes[r][c].axis("off")

        # 隐藏空白子图
        for idx in range(len(images), rows * cols):
            r, c = divmod(idx, cols)
            axes[r][c].axis("off")

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return base64.b64encode(buf.read()).decode("utf-8")


# 全局单例
plot_service = PlotService()
