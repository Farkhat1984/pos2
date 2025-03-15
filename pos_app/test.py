# Вы можете выполнить этот скрипт Python для проверки API:

import subprocess
import sys


def test_api_with_curl():
    # Команда curl для проверки API
    curl_command = [
        'curl',
        '-X', 'POST',
        '-H', 'accept: application/json',
        '-H', 'Content-Type: application/json',
        '-d', '{"username": "faragj", "password": "Ckdshfh231161!"}',
        'https://leema.kz/auth/token'
    ]

    print("Выполнение команды curl для проверки API...")
    print(" ".join(curl_command))

    try:
        # Выполнение curl запроса
        result = subprocess.run(
            curl_command,
            capture_output=True,
            text=True
        )

        # Вывод результатов
        print("\nРезультат запроса:")
        print(f"Код возврата: {result.returncode}")
        print(f"Стандартный вывод:")
        print(result.stdout)
        print(f"Ошибки:")
        print(result.stderr)

    except Exception as e:
        print(f"Ошибка при выполнении curl: {str(e)}")


if __name__ == "__main__":
    test_api_with_curl()