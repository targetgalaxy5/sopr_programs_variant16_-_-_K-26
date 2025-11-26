#!/usr/bin/env python3
\"\"\"Variant 16 — coroutine that reads floats and returns arithmetic mean of last 3.
Zeros are ignored, but a zero causes the coroutine to pause; it must not be resumed
within 1 second after receiving zero. The coroutine does not block or sleep.
\"\"\"
from typing import Generator, Optional
import sys
import time

def avg_coroutine() -> Generator[Optional[float], float, None]:
    \"\"\"Coroutine (generator) that accepts float values via .send(value).
    It yields the current average of the last three (non-zero) values after processing each input.
    Behavior on zero input:
      - zero is ignored (not added to buffer)
      - coroutine enters 'paused' state and records timestamp
      - if resumed (a .send happens) sooner than 1 second after the zero, it raises RuntimeError
      - coroutine never calls sleep/blocking functions
    \"\"\"
    buffer = []  # store last up to 3 non-zero floats
    paused = False
    last_zero_time = 0.0

    try:
        while True:
            # receive a value from sender
            value = yield None  # initial yield to accept first .send()
            now = time.monotonic()

            # If value is exactly 0.0 -> enter paused state, ignore zero
            if value == 0.0:
                paused = True
                last_zero_time = now
                # do not include zero in buffer, do not yield average for this input
                # remain active to receive next .send(), but will enforce the 1s rule on resume
                continue

            # If currently paused, check elapsed time since zero
            if paused:
                elapsed = now - last_zero_time
                if elapsed < 1.0:
                    raise RuntimeError(f\"Відновлення заборонене: лише {elapsed:.3f}s пройшло з моменту нуля (<1s)\")
                # otherwise allow resume
                paused = False

            # Normal processing: ignore any zeros, update buffer
            if value != 0.0:
                buffer.append(value)
                if len(buffer) > 3:
                    buffer.pop(0)

            # Compute average of available values in buffer (if any)
            if len(buffer) == 0:
                avg = None
            else:
                avg = sum(buffer) / len(buffer)

            # yield the current average back to caller
            yield avg

    except GeneratorExit:
        # cleanup if generator is closed
        return
    except Exception:
        raise


def main():
    coro = avg_coroutine()
    # prime the coroutine
    next(coro)

    print(\"Variant 16 — вхід: дійсні числа. Нулі зупиняють сопрограму (не враховуються). Після нуля — відновлення через >=1s.\") 
    print(\"Вводьте числа по одному на рядок. Завершити: EOF (Ctrl+D Linux/macOS, Ctrl+Z Windows).\") 
    print(\"--------------------------------------------------------------\")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            value = float(line.replace(',', '.'))
        except ValueError:
            print(f\"Неможливо розпізнати число: {line}\")
            continue

        try:
            result = coro.send(value)
            # The coroutine yields None immediately on priming or when not producing avg for that input
            if result is None:
                # try to get next yielded avg (the coroutine may have yielded None first then avg)
                # Use `next()` workaround: send a dummy to advance? Instead, after .send the generator yields either None or avg.
                # In our design, .send returns the yielded value. If None, we just indicate no avg produced.
                print(f\"(вхід {value}) — середнього ще немає або це нуль/стан паузи\")
            else:
                print(f\"(вхід {value}) -> середнє останніх {len([x for x in coro.gi_frame.f_locals.get('buffer', [])])} = {result}\")
        except RuntimeError as e:
            print(f\"Помилка: {e}\")
        except StopIteration:
            print(\"Сопрограма завершилася.\")
            break
        except Exception as e:
            print(f\"Несподівана помилка: {e}\")


if __name__ == '__main__':
    main()
