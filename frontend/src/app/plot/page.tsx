'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Upload, Download, BarChart3, Loader2, TrendingUp, ScatterChart, LayoutGrid, Grid3X3 } from 'lucide-react';

const CHART_TYPES = [
  { value: 'bar', label: '柱状图', icon: BarChart3 },
  { value: 'line', label: '折线图', icon: TrendingUp },
  { value: 'scatter', label: '散点图', icon: ScatterChart },
  { value: 'box', label: '箱线图', icon: LayoutGrid },
  { value: 'heatmap', label: '热力图', icon: Grid3X3 },
];

function parseCSV(text: string): { headers: string[]; rows: string[][] } {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = lines[0].split(',').map(h => h.trim());
  const rows = lines.slice(1).map(l => l.split(',').map(c => c.trim()));
  return { headers, rows };
}

export default function PlotPage() {
  const [file, setFile] = useState<File | null>(null);
  const [chartType, setChartType] = useState('bar');
  const [autoEnhance, setAutoEnhance] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [imageUrl, setImageUrl] = useState('');
  const [error, setError] = useState('');
  const [history, setHistory] = useState<string[]>([]);

  const handleGenerate = async () => {
    if (!file) return;
    setGenerating(true); setError('');
    try {
      const text = await file.text();
      let payload: Record<string, unknown> = {};

      if (file.name.endsWith('.json')) {
        payload = JSON.parse(text);
      } else {
        const { headers, rows } = parseCSV(text);
        if (headers.length < 2) throw new Error('CSV 至少需要 2 列（类别 + 数值）');
        const categories = rows.map(r => r[0] || '');
        const values = rows.map(r => parseFloat(r[1]) || 0);

        if (chartType === 'bar' || chartType === 'line') {
          payload = {
            data: { categories, values },
            config: { title: file.name.replace(/\.[^.]+$/, ''), xlabel: headers[0], ylabel: headers[1] },
          };
        } else if (chartType === 'scatter') {
          payload = {
            data: { x: values.map((_, i) => i), y: values },
            config: { title: file.name.replace(/\.[^.]+$/, ''), xlabel: headers[0], ylabel: headers[1] },
          };
        } else if (chartType === 'box') {
          payload = {
            data: { groups: [categories], values: [values] },
            config: { title: file.name.replace(/\.[^.]+$/, '') },
          };
        } else if (chartType === 'heatmap') {
          payload = {
            data: { matrix: [values] },
            config: { title: file.name.replace(/\.[^.]+$/, '') },
          };
        }
      }

      // 发送到后端对应图表端点
      const r = await api.post(`/api/v1/plot/${chartType}`, payload);

      let url = '';
      if (r.data?.image_base64) {
        url = `data:image/png;base64,${r.data.image_base64}`;
      } else if (r.data?.image_url) {
        url = r.data.image_url;
      }

      if (autoEnhance && url) {
        // 自动增强：请求后端 enhance 端点
        try {
          const base64 = url.replace(/^data:image\/\w+;base64,/, '');
          const blob = await (await fetch(url)).blob();
          const formData = new FormData();
          formData.append('image_bytes', blob);
          formData.append('dpi', '300');
          const er = await api.postFile('/api/v1/plot/enhance', formData);
          if (er.data?.image_base64) {
            url = `data:image/png;base64,${er.data.image_base64}`;
          }
        } catch { /* enhance 失败则使用原图 */ }
      }

      setImageUrl(url);
      if (url) setHistory(prev => [url, ...prev].slice(0, 10));
      if (!url) setError('后端未返回图片数据');
    } catch (e: any) { setError(e.message); }
    finally { setGenerating(false); }
  };

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold tracking-tight">配图工具</h1><p className="text-muted-foreground text-sm mt-1">数据可视化与学术图表生成</p></div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="shadow-sm">
          <CardHeader><CardTitle className="text-base">数据上传</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {file ? (
              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div><p className="font-medium text-sm">{file.name}</p><p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p></div>
                <Button variant="ghost" size="sm" onClick={() => setFile(null)}>移除</Button>
              </div>
            ) : (
              <div className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 transition-colors" onClick={() => document.getElementById('plot-file')?.click()}>
                <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-40" />
                <p className="text-sm text-muted-foreground">点击上传 CSV / JSON</p>
                <input id="plot-file" type="file" accept=".csv,.json" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) setFile(f); }} />
              </div>
            )}
            <div>
              <Label className="text-sm">图表类型</Label>
              <Select value={chartType} onValueChange={setChartType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{CHART_TYPES.map(c => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between">
              <Label className="text-sm">自动增强</Label>
              <Switch checked={autoEnhance} onCheckedChange={setAutoEnhance} />
            </div>
            <Button onClick={handleGenerate} disabled={!file || generating} className="w-full">
              {generating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <BarChart3 className="h-4 w-4 mr-2" />}
              生成图表
            </Button>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader><CardTitle className="text-base">预览</CardTitle></CardHeader>
          <CardContent>
            {error && <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm mb-4">{error}</div>}
            {generating ? (
              <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>
            ) : imageUrl ? (
              <div className="space-y-4">
                <img src={imageUrl} alt="Generated chart" className="w-full rounded-lg border" />
                <Button variant="outline" className="w-full" asChild><a href={imageUrl} download><Download className="h-4 w-4 mr-2" />下载图片</a></Button>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 text-muted-foreground"><p>上传数据并生成图表后在此预览</p></div>
            )}
          </CardContent>
        </Card>
      </div>

      {history.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader><CardTitle className="text-base">生成历史</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {history.map((url, i) => (
                <img key={i} src={url} alt={`Chart ${i + 1}`} className="h-24 w-36 object-cover rounded-lg border cursor-pointer hover:ring-2 ring-blue-500 shrink-0" onClick={() => setImageUrl(url)} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
