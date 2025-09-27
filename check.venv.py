import sys
import os
import subprocess

print("🔍 DIAGNÓSTICO DE ENTORNO VIRTUAL")
print("=" * 50)

# 1. Información de Python
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.prefix}")
print(f"Virtual env detected: {hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)}")

# 2. Variables de entorno
venv_path = os.environ.get('VIRTUAL_ENV', 'No activo')
print(f"VIRTUAL_ENV: {venv_path}")

# 3. Verificar entornos existentes
print("\n📁 Entornos virtuales encontrados:")
for venv_dir in ['.venv', 'venv']:
    if os.path.exists(venv_dir):
        python_path = os.path.join(venv_dir, 'bin', 'python') if os.name != 'nt' else os.path.join(venv_dir, 'Scripts', 'python.exe')
        if os.path.exists(python_path):
            print(f"✅ {venv_dir} - EXISTE y tiene Python")
        else:
            print(f"⚠️  {venv_dir} - EXISTE pero Python no encontrado")
    else:
        print(f"❌ {venv_dir} - NO EXISTE")

# 4. Verificar paquetes instalados
try:
    result = subprocess.run([sys.executable, '-m', 'pip', 'list'], capture_output=True, text=True)
    print(f"\n📦 Paquetes en el entorno actual:")
    print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
except Exception as e:
    print(f"Error checking packages: {e}")