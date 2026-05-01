import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract CSS
css_match = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
if css_match:
    with open('css/style.css', 'w', encoding='utf-8') as f:
        f.write(css_match.group(1).strip())

# Extract JS
js_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if js_match:
    js_content = js_match.group(1)
    with open('js/app.js', 'w', encoding='utf-8') as f:
        f.write(js_content.strip())

# Rewrite HTML
html_new = re.sub(r'<style>.*?</style>', '<link rel="stylesheet" href="css/style.css"/>', html, flags=re.DOTALL)
html_new = re.sub(r'<script>.*?</script>', '<script src="js/app.js"></script>', html_new, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_new)

print('Refactored frontend files successfully.')
