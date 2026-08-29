import { execFileSync } from 'node:child_process';
import { Page } from '@playwright/test';

const API = 'http://127.0.0.1:8111';

export function tokenPara(userId: string): string {
  const codigo = [
    'from app.core.auth import issue_access_token',
    `print(issue_access_token('${userId}'))`,
  ].join('; ');

  return execFileSync('python', ['-c', codigo], {
    cwd: '../backend',
    encoding: 'utf8',
  })
    .split('\n')[0]
    .trim();
}

export async function entrarComo(page: Page, userId: string): Promise<void> {
  const acesso = tokenPara(userId);

  await page.addInitScript(
    ([a, uid]) => {
      localStorage.setItem('fiance_access_token', a);
      localStorage.setItem(
        'fiance_user',
        JSON.stringify({ id: uid, email: `${uid}@e2e.local`, name: 'Teste', picture: '' })
      );
    },
    [acesso, userId]
  );
}

export async function salvarPosicao(
  page: Page,
  userId: string,
  ticker: string,
  quantidade: number,
  preco: number
): Promise<void> {
  const resposta = await page.request.post(`${API}/api/portfolio/position`, {
    headers: { Authorization: `Bearer ${tokenPara(userId)}` },
    data: { ticker, quantity: quantidade, avg_price: preco },
  });

  if (!resposta.ok()) {
    throw new Error(`falha ao semear ${ticker}: ${resposta.status()} ${await resposta.text()}`);
  }
}
