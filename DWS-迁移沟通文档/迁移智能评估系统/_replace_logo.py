import sys
sys.stdout.reconfigure(encoding='utf-8')

# === 迁移评估系统 Logo ===
path1 = r'C:\Users\52985\Desktop\04-技术文档\DWS-迁移沟通文档\迁移智能评估系统\templates\base.html'
with open(path1, 'r', encoding='utf-8') as f:
    c = f.read()

old1 = '<span class="logo-icon">&#x26A1;</span>'
new1 = '<span class="logo-icon">'
new1 += '\n        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
new1 += '\n          <circle cx="12" cy="12" r="10"/>'
new1 += '\n          <path d="M12 6v6l4 2"/>'
new1 += '\n          <path d="M7 12h3"/><path d="M14 12h3"/>'
new1 += '\n          <path d="M7 16h10"/>'
new1 += '\n        </svg>'
new1 += '\n      </span>'

if old1 in c:
    c = c.replace(old1, new1)
    with open(path1, 'w', encoding='utf-8') as f:
        f.write(c)
    print('[OK] 迁移评估系统 logo: 时钟+分析')
else:
    print('[FAIL] 迁移评估系统: pattern not found')

# === Z-DBMate Logo ===
path2 = r'C:\Users\52985\Desktop\04-技术文档\Z-DBMate工具集\templates\base.html'
with open(path2, 'r', encoding='utf-8') as f:
    c = f.read()

old2 = '<span class="logo-icon">&#x2699;</span>'
new2 = '<span class="logo-icon">'
new2 += '\n        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
new2 += '\n          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>'
new2 += '\n          <line x1="8" y1="21" x2="16" y2="21"/>'
new2 += '\n          <line x1="12" y1="17" x2="12" y2="21"/>'
new2 += '\n          <circle cx="12" cy="10" r="2"/>'
new2 += '\n          <line x1="14" y1="8" x2="16" y2="6"/>'
new2 += '\n          <line x1="10" y1="8" x2="8" y2="6"/>'
new2 += '\n        </svg>'
new2 += '\n      </span>'

if old2 in c:
    c = c.replace(old2, new2)
    with open(path2, 'w', encoding='utf-8') as f:
        f.write(c)
    print('[OK] Z-DBMate logo: 服务器+部署')
else:
    print('[FAIL] Z-DBMate: pattern not found')

print('DONE')
