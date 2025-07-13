from django.http import HttpResponse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

def debug_template_loading(request):
    template_paths = [
        'customer/address_form.html',
        'customer/templates/customer/address_form.html',
    ]
    
    results = []
    for path in template_paths:
        try:
            template = get_template(path)
            results.append(f"✓ Found template at: {path}")
        except TemplateDoesNotExist:
            results.append(f"✗ Template not found at: {path}")
    
    # Also check app_dirs finder
    from django.template.loaders.app_directories import Loader
    loader = Loader.engine
    app_template_dirs = loader.get_template_sources('customer/address_form.html')
    template_dirs = list(app_template_dirs)
    
    results.append("\nTemplate directories searched:")
    for dir in template_dirs:
        results.append(f"- {dir}")
    
    return HttpResponse("<pre>" + "\n".join(results) + "</pre>")
