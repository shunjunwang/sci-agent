"""
P0-H: 科研绘图 Skill — PlotService 单元测试

至少 10 个测试，匹配 PlotService 实际方法签名。
"""
import base64
import random

import pytest

import matplotlib
matplotlib.use('Agg')

from app.services.plot_service import PlotService


@pytest.fixture
def ps():
    return PlotService()


class TestBarChart:

    def test_bar_basic(self, ps):
        result = ps.bar_chart(
            categories=["A", "B", "C"],
            values=[10.0, 20.0, 15.0],
            errors=[1.0, 2.0, 1.5],
            title="Test Bar",
            xlabel="Group",
            ylabel="Value",
        )
        b64 = base64.b64decode(result["image_base64"])
        assert len(b64) > 100

    def test_bar_no_errors(self, ps):
        result = ps.bar_chart(categories=["X", "Y"], values=[5, 8], title="No Error")
        assert len(base64.b64decode(result["image_base64"])) > 100

    def test_bar_custom_figsize(self, ps):
        result = ps.bar_chart(
            categories=["A"], values=[1.0], figsize=(12, 8)
        )
        assert len(base64.b64decode(result["image_base64"])) > 100

    def test_bar_custom_color(self, ps):
        result = ps.bar_chart(
            categories=["A", "B"], values=[3, 7], color_palette="viridis"
        )
        assert len(base64.b64decode(result["image_base64"])) > 100

    def test_bar_empty_data(self, ps):
        result = ps.bar_chart(categories=[], values=[], title="Empty")
        assert len(base64.b64decode(result["image_base64"])) > 100


class TestLineChart:

    def test_line_basic(self, ps):
        result = ps.line_chart(
            x=[1, 2, 3, 4, 5],
            series=[
                {"label": "S1", "values": [1, 4, 9, 16, 25]},
                {"label": "S2", "values": [2, 3, 5, 7, 11]},
            ],
            title="Line Test",
            xlabel="Epoch",
            ylabel="Loss",
        )
        assert len(base64.b64decode(result["image_base64"])) > 100


class TestBoxPlot:

    def test_box_basic(self, ps):
        result = ps.box_plot(
            groups={
                "Group A": [1.0, 2.0, 3.0, 4.0, 5.0],
                "Group B": [2.0, 3.0, 4.0, 5.0, 6.0],
            },
            title="Box Test",
        )
        assert len(base64.b64decode(result["image_base64"])) > 100


class TestHeatmap:

    def test_heatmap_basic(self, ps):
        result = ps.heatmap(
            matrix=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            row_labels=["R1", "R2", "R3"],
            col_labels=["C1", "C2", "C3"],
            title="Heatmap",
        )
        assert len(base64.b64decode(result["image_base64"])) > 100


class TestVolcanoPlot:

    def test_volcano_basic(self, ps):
        random.seed(42)
        n = 50
        genes = [f"Gene{i}" for i in range(n)]
        log2fc = [random.uniform(-5, 5) for _ in range(n)]
        pvalues = [random.uniform(0.001, 0.5) for _ in range(n)]
        pvalues[0] = 0.0001
        log2fc[0] = 3.5

        result = ps.volcano_plot(
            genes=genes, log2fc=log2fc, pvalues=pvalues, title="Volcano"
        )
        assert len(base64.b64decode(result["image_base64"])) > 100


class TestCustomRender:

    def test_custom_simple(self, ps):
        code = (
            "import matplotlib.pyplot as plt\n"
            "fig, ax = plt.subplots()\n"
            "ax.plot([1, 2, 3], [1, 4, 9])\n"
            "ax.set_title('Custom Plot')\n"
        )
        result = ps.render_matplotlib(code)
        assert len(base64.b64decode(result["image_base64"])) > 100

    def test_custom_with_data(self, ps):
        code = (
            "import matplotlib.pyplot as plt\n"
            "fig, ax = plt.subplots()\n"
            "ax.plot(data['x'], data['y'], 'o-')\n"
            "ax.set_title('Data-Driven')\n"
        )
        data = {"x": [1, 2, 3], "y": [2, 4, 6]}
        result = ps.render_matplotlib(code, data=data)
        assert len(base64.b64decode(result["image_base64"])) > 100
