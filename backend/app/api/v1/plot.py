"""
P0-H: 科研绘图 Skill — API 端点
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.v1.deps import get_current_user
from app.schemas.common import APIResponse
from app.schemas.plot import (
    BarRequest,
    LineRequest,
    BoxRequest,
    HeatmapRequest,
    VolcanoRequest,
    CustomPlotRequest,
    PlotResponse,
    TemplateInfo,
)
from app.services.plot_service import plot_service, PlotServiceError

router = APIRouter(prefix="/plot", tags=["科研绘图"], dependencies=[Depends(get_current_user)])


def _handle_plot(result: Dict[str, Any]) -> APIResponse[PlotResponse]:
    """统一包装绘图结果。"""
    return APIResponse(
        code=200,
        message="success",
        data=PlotResponse(**result),
    )


# ── 柱状图 ────────────────────────────────────────


@router.post("/bar", response_model=APIResponse[PlotResponse])
async def bar_chart(req: BarRequest) -> APIResponse[PlotResponse]:
    """柱状图：组间比较、误差棒。"""
    try:
        result = plot_service.bar_chart(
            categories=req.data.categories,
            values=req.data.values,
            errors=req.data.errors,
            title=req.config.title,
            xlabel=req.config.xlabel,
            ylabel=req.config.ylabel,
            color_palette=req.config.color_palette,
            figsize=tuple(req.config.figsize),
        )
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422 if "不一致" in e.message else 400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 折线图 ────────────────────────────────────────


@router.post("/line", response_model=APIResponse[PlotResponse])
async def line_chart(req: LineRequest) -> APIResponse[PlotResponse]:
    """折线图：趋势、多系列对比。"""
    try:
        result = plot_service.line_chart(
            x=req.data.x,
            series=[s.model_dump() for s in req.data.series],
            title=req.config.title,
            xlabel=req.config.xlabel,
            ylabel=req.config.ylabel,
            figsize=tuple(req.config.figsize),
        )
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422 if "不一致" in e.message else 400, detail=e.message)


# ── 箱线图 ────────────────────────────────────────


@router.post("/box", response_model=APIResponse[PlotResponse])
async def box_plot(req: BoxRequest) -> APIResponse[PlotResponse]:
    """箱线图：分布、离群值。"""
    try:
        result = plot_service.box_plot(
            groups=req.data.groups,
            title=req.config.title,
            xlabel=req.config.xlabel,
            ylabel=req.config.ylabel,
            figsize=tuple(req.config.figsize),
        )
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422 if "不一致" in e.message else 400, detail=e.message)


# ── 热力图 ────────────────────────────────────────


@router.post("/heatmap", response_model=APIResponse[PlotResponse])
async def heatmap(req: HeatmapRequest) -> APIResponse[PlotResponse]:
    """热力图：相关性矩阵、表达量。"""
    try:
        result = plot_service.heatmap(
            matrix=req.data.matrix,
            row_labels=req.data.row_labels,
            col_labels=req.data.col_labels,
            title=req.config.title,
            cmap=req.config.cmap,
            annot=req.config.annot,
            figsize=tuple(req.config.figsize),
        )
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422 if "不一致" in e.message else 400, detail=e.message)


# ── 火山图 ────────────────────────────────────────


@router.post("/volcano", response_model=APIResponse[PlotResponse])
async def volcano_plot(req: VolcanoRequest) -> APIResponse[PlotResponse]:
    """火山图：差异表达分析。"""
    try:
        result = plot_service.volcano_plot(
            genes=req.data.genes,
            log2fc=req.data.log2fc,
            pvalues=req.data.pvalues,
            title=req.config.title,
            fc_threshold=req.config.fc_threshold,
            pvalue_threshold=req.config.pvalue_threshold,
            figsize=tuple(req.config.figsize),
        )
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422 if "不一致" in e.message else 400, detail=e.message)


# ── 自定义绘图 ────────────────────────────────────


@router.post("/custom", response_model=APIResponse[PlotResponse])
async def custom_plot(req: CustomPlotRequest) -> APIResponse[PlotResponse]:
    """自定义绘图：执行 matplotlib Python 代码。"""
    try:
        result = plot_service.render_matplotlib(code=req.code, data=req.data)
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422, detail=e.detail)


# ── P0-L: 论文配图自动化扩展 ────────────────────────


@router.post("/enhance", response_model=APIResponse[PlotResponse])
async def enhance_plot(
    image_bytes: bytes = File(...),
    dpi: int = Form(300),
) -> APIResponse[PlotResponse]:
    """自动增强：提升沙箱原始图表为发表级质量。"""
    try:
        config = {"dpi": dpi}
        result = plot_service.auto_enhance(image_bytes, config)
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422, detail=e.detail)


@router.post("/panel", response_model=APIResponse[PlotResponse])
async def figure_panel(
    images: List[UploadFile] = File(...),
    rows: int = Form(1),
    cols: int = Form(1),
    labels: str = Form(""),
    dpi: int = Form(300),
) -> APIResponse[PlotResponse]:
    """多图拼接面板。"""
    try:
        label_list = [l.strip() for l in labels.split(",") if l.strip()]
        if not label_list:
            label_list = [f"({chr(97 + i)})" for i in range(len(images))]

        image_data = [await img.read() for img in images]
        result = plot_service.create_figure_panel(
            image_data, layout=(rows, cols), labels=label_list, dpi=dpi,
        )
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422, detail=e.detail)


@router.post("/grayscale", response_model=APIResponse[PlotResponse])
async def grayscale_plot(
    image_bytes: bytes = File(...),
) -> APIResponse[PlotResponse]:
    """转换为灰度图。"""
    try:
        result = plot_service.convert_to_grayscale(image_bytes)
        return _handle_plot(result)
    except PlotServiceError as e:
        raise HTTPException(status_code=422, detail=e.detail)


# ── 模板信息 ──────────────────────────────────────


@router.get("/templates", response_model=APIResponse[list])
async def list_templates() -> APIResponse[list]:
    """获取所有绘图模板说明和参数格式。"""
    templates = plot_service.get_templates()
    return APIResponse(code=200, message="success", data=templates)
