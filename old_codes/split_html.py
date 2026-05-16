import re
import os

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Extract CSS
style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
if style_match:
    css = style_match.group(1).strip()
    os.makedirs("frontend/css", exist_ok=True)
    with open("frontend/css/main.css", "w", encoding="utf-8") as f:
        f.write(css)

# Extract JS
script_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
if script_match:
    js = script_match.group(1).strip()
    os.makedirs("frontend/js", exist_ok=True)
    with open("frontend/js/app.js", "w", encoding="utf-8") as f:
        f.write(js)

# Update HTML
new_content = re.sub(r'<style>.*?</style>', '<link rel="stylesheet" href="/css/main.css">', content, flags=re.DOTALL)
new_content = re.sub(r'<script>.*?</script>', '<script src="/js/app.js"></script>', new_content, flags=re.DOTALL)

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Split completed successfully!")
