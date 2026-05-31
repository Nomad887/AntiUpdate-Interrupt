import os
import sys
import subprocess
import shutil
from pathlib import Path

# === НАСТРОЙКИ ===
REPO_NAME = "AntiUpdate-Interrupt"
RELEASE_TAG = "v1.0.0"
RELEASE_TITLE = "Release v1.0.0"
RELEASE_DESC = "тест."
BUILD_EXE = True  # True = собрать exe, False = только код

def run_cmd(cmd, check=True):
    """Запускает команду и выводит результат"""
    print(f"▶️ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Выводим stdout, если есть
    if result.stdout.strip():
        for line in result.stdout.strip().split('\n'):
            print(f"   {line}")
            
    # Если ошибка и check=True, останавливаемся
    if result.returncode != 0:
        if check:
            print(f"❌ Ошибка выполнения команды:")
            print(result.stderr.strip())
            sys.exit(1)
        else:
            print(f"⚠️  Предупреждение (не критично): {result.stderr.strip()}")
    return result

def get_gh_user():
    """Получает имя пользователя GitHub"""
    res = run_cmd("gh api user --jq .login", check=False)
    if res.returncode == 0:
        return res.stdout.strip()
    return None

def main():
    print("🤖 Запуск агента публикации AntiUpdate Interrupt...")
    
    # 1. Проверка зависимостей
    if shutil.which("gh") is None:
        print("❌ Не найден GitHub CLI (gh).")
        print("   Установите отсюда: https://cli.github.com/")
        print("   Затем выполните 'gh auth login' в терминале.")
        sys.exit(1)
        
    user = get_gh_user()
    if not user:
        print("❌ Не удалось получить имя пользователя GitHub. Вы уверены, что выполнили 'gh auth login'?")
        sys.exit(1)
        
    print(f"✅ Авторизован как: {user}")

    # 2. Инициализация Git (если ещё не init)
    if not Path(".git").exists():
        print("📂 Инициализация Git репозитория...")
        run_cmd("git init")
        run_cmd("git add .")
        # Проверяем, есть ли что коммитить
        res = run_cmd("git status --porcelain", check=False)
        if not res.stdout.strip():
            print("⚠️  Нет изменений для коммита. Проверьте, что файлы не игнорируются .gitignore")
        else:
            run_cmd(f'git commit -m "{RELEASE_TITLE}"')
    else:
        print("📂 Git репозиторий уже существует. Обновляем изменения...")
        run_cmd("git add .")
        run_cmd(f'git commit -m "{RELEASE_TITLE}" || echo "Нет новых изменений"')

    run_cmd("git branch -M main")

    # 3. Создание репозитория на GitHub
    # Используем простой способ: создаем пустой репо, потом пушим
    print(f"🌐 Создание репозитория '{REPO_NAME}' на GitHub...")
    
    # Проверяем, существует ли уже такой репо
    check_repo = run_cmd(f'gh repo view "{user}/{REPO_NAME}"', check=False)
    
    if check_repo.returncode != 0:
        # Репо нет, создаем
        run_cmd(f'gh repo create "{REPO_NAME}" --public --confirm')
        # Добавляем remote
        run_cmd(f'git remote add origin https://github.com/{user}/{REPO_NAME}.git')
    else:
        print("ℹ️  Репозиторий уже существует. Предполагаем, что remote настроен верно.")
        # Пробуем добавить remote, если его нет
        run_cmd(f'git remote add origin https://github.com/{user}/{REPO_NAME}.git', check=False)

    # 4. Push кода
    print("📤 Отправка кода на GitHub...")
    run_cmd("git push -u origin main")

    # 5. Сборка EXE (опционально)
    exe_path = None
    if BUILD_EXE:
        print("📦 Сборка .exe через PyInstaller...")
        # Очищаем прошлые сборки
        if Path("dist").exists():
            shutil.rmtree("dist")
        if Path("build").exists():
            shutil.rmtree("build")
            
        run_cmd('pyinstaller --onefile --windowed --name "AntiUpdate Interrupt" --icon=app.ico --noconfirm main.py')
        
        exe_path = Path("dist/AntiUpdate Interrupt.exe")
        if not exe_path.exists():
            print("❌ Файл .exe не найден после сборки. Проверьте логи выше.")
            sys.exit(1)
        print(f"✅ EXE успешно собран: {exe_path}")
    else:
        # Ищем exe в dist, если сборка была ранее
        dist_folder = Path("dist")
        if dist_folder.exists():
            exes = list(dist_folder.glob("*.exe"))
            if exes:
                exe_path = exes[0]
                print(f"✅ Найден существующий EXE: {exe_path}")

    # 6. Создание Release и загрузка файла
    print("🏷️  Создание Release...")
    
    # Удаляем тег и релиз, если они уже есть (для повторного запуска)
    run_cmd(f'gh release delete "{RELEASE_TAG}" --yes', check=False)
    run_cmd(f'git tag -d "{RELEASE_TAG}"', check=False)
    
    # Создаем новый тег локально
    run_cmd(f'git tag "{RELEASE_TAG}"')
    run_cmd(f'git push origin "{RELEASE_TAG}"')
    
    # Создаем релиз на GitHub
    run_cmd(f'gh release create "{RELEASE_TAG}" --title "{RELEASE_TITLE}" --notes "{RELEASE_DESC}"')
    
    if exe_path and exe_path.exists():
        print(f"📎 Загрузка бинарного файла...")
        run_cmd(f'gh release upload "{RELEASE_TAG}" "{exe_path}" --clobber')
    else:
        print("⚠️  EXE файл не найден, загружаем только исходный код.")

    print("\n" + "="*50)
    print("🎉 ГОТОВО!")
    print(f"🌐 Ссылка на репозиторий: https://github.com/{user}/{REPO_NAME}")
    print(f"📥 Ссылка на скачивание: https://github.com/{user}/{REPO_NAME}/releases/tag/{RELEASE_TAG}")
    print("="*50)

if __name__ == "__main__":
    main()