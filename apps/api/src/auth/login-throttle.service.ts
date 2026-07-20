import { HttpException, HttpStatus, Injectable } from '@nestjs/common';

interface AttemptWindow {
  count: number;
  startedAt: number;
}

/** Límite pequeño y deliberado para proteger la cuenta compartida del TFM. */
@Injectable()
export class LoginThrottleService {
  private readonly attempts = new Map<string, AttemptWindow>();
  private readonly maximum = Number(process.env.LOGIN_MAX_ATTEMPTS || 5);
  private readonly windowMs = Number(process.env.LOGIN_WINDOW_SECONDS || 60) * 1000;

  assertAllowed(key: string): void {
    const current = this.current(key);
    if (current && current.count >= this.maximum) {
      throw new HttpException('Demasiados intentos. Espera un minuto antes de volver a probar.', HttpStatus.TOO_MANY_REQUESTS);
    }
  }

  registerFailure(key: string): void {
    const current = this.current(key);
    this.attempts.set(key, current
      ? { ...current, count: current.count + 1 }
      : { count: 1, startedAt: Date.now() });
  }

  clear(key: string): void {
    this.attempts.delete(key);
  }

  private current(key: string): AttemptWindow | undefined {
    const value = this.attempts.get(key);
    if (value && Date.now() - value.startedAt >= this.windowMs) {
      this.attempts.delete(key);
      return undefined;
    }
    return value;
  }
}
