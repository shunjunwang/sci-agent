'use client';
import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { User, Key, Palette, Info } from 'lucide-react';

const SECTIONS = [
  { id: 'profile', label: '个人信息', icon: User },
  { id: 'apikey', label: 'API Key', icon: Key },
  { id: 'appearance', label: '外观', icon: Palette },
  { id: 'about', label: '关于', icon: Info },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const [section, setSection] = useState('profile');
  const [saved, setSaved] = useState(false);

  const current = SECTIONS.find(s => s.id === section);

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold tracking-tight">设置</h1></div>

      <div className="flex gap-6">
        <Card className="w-48 shrink-0 shadow-sm h-fit">
          <CardContent className="p-2">
            <nav className="space-y-1">
              {SECTIONS.map(s => (
                <button key={s.id} onClick={() => setSection(s.id)} className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${section === s.id ? 'bg-slate-100 dark:bg-slate-800 font-medium' : 'text-muted-foreground hover:bg-slate-50 dark:hover:bg-slate-900'}`}>
                  <s.icon className="h-4 w-4" />{s.label}
                </button>
              ))}
            </nav>
          </CardContent>
        </Card>

        <Card className="flex-1 shadow-sm">
          <CardHeader><CardTitle>{current?.label}</CardTitle><CardDescription>{current?.id === 'profile' ? '管理你的个人资料' : current?.id === 'apikey' ? '管理 API 密钥' : current?.id === 'appearance' ? '自定义界面外观' : '关于 SciAgent'}</CardDescription></CardHeader>
          <CardContent>
            {section === 'profile' && (
              <div className="space-y-4">
                <div><Label>姓名</Label><Input defaultValue={user?.full_name || ''} /></div>
                <div><Label>邮箱</Label><Input defaultValue={user?.email || ''} disabled /></div>
                <div><Label>新密码</Label><Input type="password" placeholder="留空不修改" /></div>
                <Button onClick={() => setSaved(true)}>保存修改</Button>
                {saved && <p className="text-sm text-green-600">已保存</p>}
              </div>
            )}
            {section === 'apikey' && (
              <div className="space-y-4">
                <div><Label>OpenAI API Key</Label><Input type="password" placeholder="sk-..." /></div>
                <div><Label>arXiv API</Label><Input placeholder="可选" /></div>
                <div><Label>Semantic Scholar API Key</Label><Input placeholder="可选" /></div>
                <Button onClick={() => setSaved(true)}>保存密钥</Button>
                {saved && <p className="text-sm text-green-600">已保存</p>}
              </div>
            )}
            {section === 'appearance' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between"><Label>深色模式</Label><Switch onCheckedChange={(v) => document.documentElement.classList.toggle('dark', v)} /></div>
                <div className="flex items-center justify-between"><Label>紧凑布局</Label><Switch /></div>
                <Separator />
                <p className="text-sm text-muted-foreground">主题：New York (shadcn/ui)</p>
              </div>
            )}
            {section === 'about' && (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">版本</span><span>0.1.0</span></div>
                <Separator />
                <div className="flex justify-between"><span className="text-muted-foreground">前端框架</span><span>Next.js 16 + React 19</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">UI组件库</span><span>shadcn/ui (New York)</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">样式</span><span>Tailwind CSS v4</span></div>
                <Separator />
                <div className="flex justify-between"><span className="text-muted-foreground">后端API</span><span>FastAPI @ localhost:8000</span></div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
