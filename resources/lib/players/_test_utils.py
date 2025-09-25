import traceback
from typing import Callable, List, Tuple

# Definiujemy typ, aby kod był czytelniejszy
PlayerFunction = Callable[[str], Tuple[str | None, str | None, dict | None]]

def run_tests(player_function: PlayerFunction, test_urls: List[str]):
    """
    Uruchamia serię testów dla danej, synchronicznej funkcji playera.
    Ta funkcja jest przeznaczona do uruchamiania bezpośrednio z linii poleceń
    w celach deweloperskich i debugowania.
    """
    if not test_urls:
        print(f"No test URLs provided for {player_function.__name__}.")
        return

    for test_url in test_urls:
        print("-" * 60)
        print(f"Testing Player : {player_function.__name__}")
        print(f"Testing URL    : {test_url}")
        print("-" * 60)

        try:
            # Bezpośrednie, synchroniczne wywołanie funkcji playera
            video_link, video_quality, video_headers = player_function(test_url)

            if video_link:
                print("\n✅ --- SUCCESS --- ✅")
                print(f"  URL     : {video_link}")
                print(f"  Quality : {video_quality}")
                print(f"  Headers : {video_headers}")
            else:
                print("\n❌ --- FAILURE --- ❌")
                print("  Function returned None, but no exception was raised.")

        except Exception as e:
            print(f"\n💥 --- CRITICAL FAILURE --- 💥")
            print(f"  An exception occurred during the test: {e}")
            print("\n--- TRACEBACK ---")
            traceback.print_exc()
            print("-------------------")

        print("\n" * 2)