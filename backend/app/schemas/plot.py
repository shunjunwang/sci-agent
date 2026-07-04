"""
P0-H: 科研绘图 Skill — Schema 定义
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── 柱状图 ────────────────────────────────────────────


class BarData(BaseModel):
    """柱状图数据。"""

    categories: List[str] = Field(..., min_length=1, description="X 轴类别标签")
    values: List[float] = Field(..., min_length=1, description="Y 轴数值")
    errors: Optional[List[float]] = Field(None, description="误差棒数值（可选）")


class BarConfig(BaseModel):
    """柱状图配置。"""

    title: Optional[str] = Field(None, description="图表标题")
    xlabel: Optional[str] = Field(None, description="X 轴标签")
    ylabel: Optional[str] = Field(None, description="Y 轴标签")
    color_palette: str = Field(default="Set2", description="Seaborn 调色板名称")
    figsize: List[int] = Field(default=[10, 6], description="图表尺寸 [宽, 高]（英寸）")


class BarRequest(BaseModel):
    """柱状图请求。"""

    data: BarData
    config: BarConfig = Field(default_factory=BarConfig)


# ── 折线图 ────────────────────────────────────────────


class SeriesItem(BaseModel):
    """折线图单条序列。"""

    label: str = Field(..., description="序列名称")
    values: List[float] = Field(..., min_length=1, description="数据点")


class LineData(BaseModel):
    """折线图数据。"""

    x: List[Any] = Field(..., min_length=1, description="X 轴数值")
    series: List[SeriesItem] = Field(..., min_length=1, description="数据序列列表")


class LineConfig(BaseModel):
    """折线图配置。"""

    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    figsize: List[int] = Field(default=[10, 6])


class LineRequest(BaseModel):
    """折线图请求。"""

    data: LineData
    config: LineConfig = Field(default_factory=LineConfig)


# ── 箱线图 ────────────────────────────────────────────


class BoxData(BaseModel):
    """箱线图数据。"""

    groups: Dict[str, List[float]] = Field(..., min_length=1, description="{组名: [数值列表]}")


class BoxConfig(BaseModel):
    """箱线图配置。"""

    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    figsize: List[int] = Field(default=[10, 6])


class BoxRequest(BaseModel):
    """箱线图请求。"""

    data: BoxData
    config: BoxConfig = Field(default_factory=BoxConfig)


# ── 热力图 ────────────────────────────────────────────


class HeatmapData(BaseModel):
    """热力图数据。"""

    matrix: List[List[float]] = Field(..., min_length=1, description="二维数值矩阵")
    row_labels: Optional[List[str]] = Field(None, description="行标签")
    col_labels: Optional[List[str]] = Field(None, description="列标签")


class HeatmapConfig(BaseModel):
    """热力图配置。"""

    title: Optional[str] = None
    cmap: str = Field(default="viridis", description="颜色映射名称")
    annot: bool = Field(default=True, description="是否标注数值")
    figsize: List[int] = Field(default=[10, 8])


class HeatmapRequest(BaseModel):
    """热力图请求。"""

    data: HeatmapData
    config: HeatmapConfig = Field(default_factory=HeatmapConfig)


# ── 火山图 ────────────────────────────────────────────


class VolcanoData(BaseModel):
    """火山图数据。"""

    genes: List[str] = Field(..., min_length=1, description="基因名称列表")
    log2fc: List[float] = Field(..., min_length=1, description="log2 Fold Change")
    pvalues: List[float] = Field(..., min_length=1, description="p 值列表")


class VolcanoConfig(BaseModel):
    """火山图配置。"""

    title: Optional[str] = None
    fc_threshold: float = Field(default=1.0, description="Fold Change 阈值（log2）")
    pvalue_threshold: float = Field(default=0.05, description="显著性阈值")
    figsize: List[int] = Field(default=[10, 8])


class VolcanoRequest(BaseModel):
    """火山图请求。"""

    data: VolcanoData
    config: VolcanoConfig = Field(default_factory=VolcanoConfig)


# ── 自定义绘图 ────────────────────────────────────────


class CustomPlotRequest(BaseModel):
    """自定义绘图请求。"""

    code: str = Field(..., min_length=1, description="matplotlib Python 代码")
    data: Optional[Dict[str, Any]] = Field(None, description="注入到代码的 data 变量")


# ── 通用响应 ──────────────────────────────────────────


class PlotResponse(BaseModel):
    """绘图响应。"""

    image_base64: str = Field(..., description="Base64 编码的 PNG 图片")
    format: str = Field(default="png")
    dpi: int = Field(default=300)
    width: int = Field(default=1000)
    height: int = Field(default=600)


class TemplateInfo(BaseModel):
    """模板描述。"""

    name: str
    endpoint: str
    description: str
    data_schema: dict
    config_schema: dict
