import { provideHttpClient } from '@angular/common/http';
import { PLATFORM_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from './auth.service';

function em(plataforma: 'server' | 'browser'): AuthService {
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [provideHttpClient(), { provide: PLATFORM_ID, useValue: plataforma }],
  });
  return TestBed.inject(AuthService);
}

function googleFalso() {
  const renderButton = vi.fn();
  const initialize = vi.fn();
  (window as unknown as Record<string, unknown>)['google'] = {
    accounts: { id: { initialize, renderButton } },
  };
  return { renderButton, initialize };
}

const container = { nodeType: 1 } as unknown as HTMLElement;

afterEach(() => {
  delete (window as unknown as Record<string, unknown>)['google'];
  vi.useRealTimers();
});

describe('AuthService quando o Angular renderiza no servidor', () => {
  it('renderGoogleButton não desenha nada e não agenda repetição', () => {
    const { renderButton } = googleFalso();
    vi.useFakeTimers();
    const auth = em('server');

    auth.renderGoogleButton(container);
    vi.advanceTimersByTime(2000);

    expect(renderButton).not.toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('no navegador ele desenha — senão a guarda teria matado o login', () => {
    const { renderButton } = googleFalso();
    const auth = em('browser');

    auth.renderGoogleButton(container);

    expect(renderButton).toHaveBeenCalledOnce();
  });

  it('token e refresh não estouram sem localStorage', () => {
    const auth = em('server');

    expect(auth.token()).toBeNull();
    expect(auth.refreshToken()).toBeNull();
  });
});
