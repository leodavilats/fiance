import { expect, test, type Page } from '@playwright/test';
import { entrarComo, tokenPara } from './sessao';

const API = 'http://127.0.0.1:8111';

async function lancar(page: Page, userId: string, corpo: Record<string, unknown>): Promise<number> {
  const resposta = await page.request.post(`${API}/api/cashflow/entries`, {
    headers: { Authorization: `Bearer ${tokenPara(userId)}` },
    data: corpo,
  });
  if (!resposta.ok()) {
    throw new Error(`falha ao lançar: ${resposta.status()} ${await resposta.text()}`);
  }
  return (await resposta.json()).id;
}

async function cadastrarDivida(
  page: Page,
  userId: string,
  corpo: Record<string, unknown>
): Promise<void> {
  const resposta = await page.request.post(`${API}/api/cashflow/debts`, {
    headers: { Authorization: `Bearer ${tokenPara(userId)}` },
    data: corpo,
  });
  if (!resposta.ok()) {
    throw new Error(`falha ao cadastrar dívida: ${resposta.status()} ${await resposta.text()}`);
  }
}

/* Um titular por execução: o banco do e2e persiste entre rodadas. */
const RODADA = Date.now().toString(36);

function titular(nome: string): string {
  return `e2e_${nome}_${RODADA}`;
}

function mesCorrente(): string {
  const agora = new Date();
  return `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, '0')}`;
}

function dia(n: number): string {
  return `${mesCorrente()}-${String(n).padStart(2, '0')}`;
}

function mesAnterior(): string {
  const agora = new Date();
  const anterior = new Date(agora.getFullYear(), agora.getMonth() - 1, 1);
  return `${anterior.getFullYear()}-${String(anterior.getMonth() + 1).padStart(2, '0')}`;
}

function diaDoAnterior(n: number): string {
  return `${mesAnterior()}-${String(n).padStart(2, '0')}`;
}

test.describe('a ponte responde em vez de perguntar', () => {
  test('sem caixa lançado, a tela diz por que não pode responder', async ({ page }) => {
    const uid = titular('sobra_vazia');
    await entrarComo(page, uid);
    await page.goto('/sobra');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Sem lançamento de caixa')).toBeVisible();
    await expect(page.getByRole('link', { name: /Lançar o mês/ })).toBeVisible();
  });

  test('com caixa lançado, a sobra sai sem nenhum campo a preencher', async ({ page }) => {
    const uid = titular('sobra_cheia');
    await entrarComo(page, uid);
    await lancar(page, uid, {
      kind: 'income',
      category: 'salario',
      description: 'Salário',
      amount: 6418.73,
      due_on: dia(5),
      paid_on: dia(5),
    });
    await lancar(page, uid, {
      kind: 'expense',
      category: 'moradia',
      description: 'Aluguel',
      amount: 2150,
      due_on: dia(5),
      paid_on: dia(5),
    });

    await page.goto('/sobra');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await expect(page.locator('main')).toContainText('4.268,73');
    await expect(
      page.locator('main input'),
      'a ponte não pede o valor do aporte a quem tem caixa: é isso que ela resolve'
    ).toHaveCount(0);
  });

  test('dívida cara vem antes do aporte, e diz o que a derrubaria', async ({ page }) => {
    const uid = titular('sobra_divida');
    await entrarComo(page, uid);
    await lancar(page, uid, {
      kind: 'income',
      category: 'salario',
      description: 'Salário',
      amount: 4000,
      due_on: dia(5),
      paid_on: dia(5),
    });
    await cadastrarDivida(page, uid, {
      kind: 'rotativo_cartao',
      description: 'Rotativo do cartão',
      balance: 890,
      monthly_rate: 14.9,
    });

    await page.goto('/sobra');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    const passos = page.locator('main ol > li');
    await expect(passos).toHaveCount(2);
    await expect(passos.nth(0)).toContainText('Dívida');
    await expect(passos.nth(1)).toContainText('Aporte');

    await passos.nth(0).getByText('O que derrubaria isto').click();
    await expect(passos.nth(0)).toContainText('ao mês');
  });

  test('dívida que come a sobra inteira termina sem aporte, e a tela diz que é resposta', async ({
    page,
  }) => {
    const uid = titular('sobra_sem_aporte');
    await entrarComo(page, uid);
    await lancar(page, uid, {
      kind: 'income',
      category: 'salario',
      description: 'Salário',
      amount: 800,
      due_on: dia(5),
      paid_on: dia(5),
    });
    await cadastrarDivida(page, uid, {
      kind: 'cheque_especial',
      description: 'Cheque especial',
      balance: 9000,
      monthly_rate: 8.2,
    });

    await page.goto('/sobra');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await expect(page.locator('main ol > li')).toHaveCount(1);
    await expect(page.locator('main')).toContainText('termina sem aporte');
  });
});

test.describe('o mês separa fato de projeção', () => {
  test('livre agora não desconta estimativa, e a conta a vencer aparece', async ({ page }) => {
    const uid = titular('mes');
    await entrarComo(page, uid);
    await lancar(page, uid, {
      kind: 'income',
      category: 'salario',
      description: 'Salário',
      amount: 6418.73,
      due_on: dia(5),
      paid_on: dia(5),
    });
    await lancar(page, uid, {
      kind: 'expense',
      category: 'contas_da_casa',
      description: 'Energia',
      amount: 187.44,
      due_on: dia(22),
    });

    await page.goto('/mes');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await expect(page.locator('main')).toContainText('6.231,29');
    await expect(page.getByText('A vencer · 1')).toBeVisible();
    await expect(page.locator('main')).toContainText('Energia');
  });

  test('marcar como paga move a conta do comprometido para o pago', async ({ page }) => {
    const uid = titular('mes_pagar');
    await entrarComo(page, uid);
    await lancar(page, uid, {
      kind: 'income',
      category: 'salario',
      description: 'Salário',
      amount: 3000,
      due_on: dia(5),
      paid_on: dia(5),
    });
    await lancar(page, uid, {
      kind: 'expense',
      category: 'contas_da_casa',
      description: 'Internet',
      amount: 129.9,
      due_on: dia(25),
    });

    await page.goto('/mes');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'Marcar como paga' }).click();
    await expect(page.getByText('A vencer ·')).toHaveCount(0);
    await expect(page.locator('main')).toContainText('2.870,10');
  });

  test('sem lançamento nenhum, o mês é a porta de entrada', async ({ page }) => {
    await entrarComo(page, titular('mes_vazio'));
    await page.goto('/mes');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('ainda não tem nada lançado')).toBeVisible();
    await expect(page.getByRole('link', { name: /Lançar o primeiro mês/ })).toBeVisible();
  });
});

test.describe('a dívida se classifica por custo, não por tipo', () => {
  test('sem taxa informada não há classe, e a tela diz isso', async ({ page }) => {
    const uid = titular('divida_sem_taxa');
    await entrarComo(page, uid);
    await cadastrarDivida(page, uid, {
      kind: 'parcelamento',
      description: 'Parcelamento da fatura',
      balance: 1200,
    });

    await page.goto('/mes/dividas');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await expect(page.locator('main')).toContainText('Sem taxa');
    await expect(page.locator('main')).toContainText('Sem a taxa não dá para comparar');
  });

  test('o mesmo tipo muda de leitura com a taxa', async ({ page }) => {
    const uid = titular('divida_por_custo');
    await entrarComo(page, uid);
    await cadastrarDivida(page, uid, {
      kind: 'credito_pessoal',
      description: 'Empréstimo caro',
      balance: 3000,
      monthly_rate: 3.5,
    });
    await cadastrarDivida(page, uid, {
      kind: 'credito_pessoal',
      description: 'Empréstimo barato',
      balance: 3000,
      monthly_rate: 0.2,
    });

    await page.goto('/mes/dividas');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    const caro = page.locator('tbody tr', { hasText: 'Empréstimo caro' });
    const barato = page.locator('tbody tr', { hasText: 'Empréstimo barato' });

    await expect(caro).toContainText('Cara');
    await expect(
      barato,
      'se o tipo decidisse, os dois sairiam iguais — é a taxa que decide'
    ).toContainText('Administrável');
  });
});

test.describe('lançar', () => {
  test('o formulário lança e o mês passa a mostrar', async ({ page }) => {
    await entrarComo(page, titular('lancar'));
    await page.goto('/mes/lancar');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.locator('#lanc-kind').selectOption('income');
    await page.locator('#lanc-categoria').selectOption('salario');
    await page.locator('#lanc-descricao').fill('Salário');
    await page.locator('#lanc-valor').fill('5000');
    await page.locator('#lanc-vencimento').fill(dia(5));
    await page.getByRole('button', { name: 'Lançar', exact: true }).click();

    await expect(page.getByText(/Lançado em/)).toBeVisible();

    await page.goto('/mes');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('main')).toContainText('5.000,00');
  });

  test('provento não está entre as categorias de entrada', async ({ page }) => {
    await entrarComo(page, titular('lancar_provento'));
    await page.goto('/mes/lancar');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.locator('#lanc-kind').selectOption('income');

    const opcoes = await page.locator('#lanc-categoria option').allTextContents();
    expect(
      opcoes,
      'provento é derivado do razão: oferecer a categoria aqui convidaria a contar o mesmo ' +
        'dinheiro duas vezes'
    ).not.toContain('Provento');
  });
});

test.describe('lançamento fora do mês corrente', () => {
  test('o formulário diz em que mês caiu, e o mês tem seletor para chegar lá', async ({ page }) => {
    await entrarComo(page, titular('mes_anterior'));
    await page.goto('/mes/lancar');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await page.locator('#lanc-descricao').fill('Mercado de agosto');
    await page.locator('#lanc-valor').fill('231.47');
    await page.locator('#lanc-vencimento').fill('2026-08-31');
    await page.locator('#lanc-pagamento').fill('2026-08-31');
    await page.getByRole('button', { name: 'Lançar' }).click();

    await expect(
      page.getByText('Lançado em agosto de 2026'),
      'dizer só "Lançado." esconde que o lançamento foi para um mês que a pessoa não está vendo'
    ).toBeVisible();

    await page.getByRole('link', { name: /Ver agosto de 2026/ }).click();
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/[?&]mes=2026-08/);
    await expect(
      page.locator('main'),
      'o recorte mora na URL, e a tela do mês escolhido mostra o que foi lançado nele'
    ).toContainText('Mercado de agosto');
  });

  test('o mês corrente vazio diz que há lançamento em outro mês', async ({ page }) => {
    const uid = titular('mes_vazio_com_outro');
    await entrarComo(page, uid);
    await lancar(page, uid, {
      kind: 'expense',
      category: 'mercado',
      description: 'Feira de agosto',
      amount: 120.5,
      due_on: '2026-08-20',
      paid_on: '2026-08-20',
    });

    await page.goto('/mes');
    await expect(page.locator('header')).toBeVisible();
    await page.waitForLoadState('networkidle');

    await expect(
      page.locator('main'),
      'mês corrente sem nada, com lançamento em outro mês, tem de dizer isso — e não ficar mudo'
    ).toContainText('lançamentos em outros meses');
  });
});

test.describe('editar um lançamento', () => {
  test('o valor errado se corrige na própria linha, sem virar dois lançamentos', async ({
    page,
  }) => {
    const uid = titular('editar');
    await entrarComo(page, uid);
    await lancar(page, uid, {
      kind: 'expense',
      category: 'moradia',
      description: 'Aluguel',
      amount: 2150,
      due_on: dia(5),
      paid_on: dia(5),
    });

    await page.goto('/mes');
    await page.waitForLoadState('networkidle');

    await page.getByRole('link', { name: 'Editar' }).first().click();
    await expect(page).toHaveURL(/editar=/);
    await expect(page.getByRole('heading', { name: 'Editar lançamento' })).toBeVisible();

    await expect(page.locator('#lanc-descricao')).toHaveValue('Aluguel');
    await page.locator('#lanc-valor').fill('2250');
    await page.getByRole('button', { name: 'Salvar' }).click();

    await expect(page).toHaveURL(/\/mes/);
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('cell', { name: 'Aluguel' })).toHaveCount(1);
    await expect(page.getByText('R$ 2.250,00').first()).toBeVisible();
  });

  test('provento derivado do razão não oferece edição', async ({ page }) => {
    const uid = titular('editar_derivado');
    await entrarComo(page, uid);
    await lancar(page, uid, {
      kind: 'expense',
      category: 'moradia',
      description: 'Aluguel',
      amount: 2150,
      due_on: dia(5),
      paid_on: dia(5),
    });

    await page.goto('/mes');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('link', { name: 'Editar' })).toHaveCount(1);
  });
});

test.describe('entrada não tem vencimento', () => {
  test('o tipo entrada pede um dia só, e nenhum campo de vencimento', async ({ page }) => {
    const uid = titular('entrada_sem_vencimento');
    await entrarComo(page, uid);
    await page.goto('/mes/lancar');
    await page.waitForLoadState('networkidle');

    const rotulo = page.locator('label[for="lanc-vencimento"]');
    await expect(rotulo).toHaveText(/Vencimento/);

    await page.locator('#lanc-kind').selectOption('income');

    await expect(
      rotulo,
      'entrada não vence: exigir uma data de vencimento para dinheiro que se recebe é pedir ' +
        'um dado que não existe'
    ).toHaveText('Dia');
    await expect(page.locator('#lanc-pagamento')).toHaveCount(0);
  });

  test('a entrada lançada com um dia só conta no mês', async ({ page }) => {
    const uid = titular('entrada_um_dia');
    await entrarComo(page, uid);
    await page.goto('/mes/lancar');
    await page.waitForLoadState('networkidle');

    await page.locator('#lanc-kind').selectOption('income');
    await page.locator('#lanc-categoria').selectOption('salario');
    await page.locator('#lanc-descricao').fill('Salário');
    await page.locator('#lanc-valor').fill('6418.73');
    await page.locator('#lanc-vencimento').fill(dia(5));
    await page.getByRole('button', { name: 'Lançar', exact: true }).click();

    await expect(page.getByText(/Lançado em/)).toBeVisible();

    await page.goto('/mes');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('R$ 6.418,73').first()).toBeVisible();
  });
});

test.describe('o mês anterior serve de molde', () => {
  test('o fixo vem marcado, o variável não, e o copiado nasce a vencer', async ({ page }) => {
    const uid = titular('molde');
    await entrarComo(page, uid);

    await lancar(page, uid, {
      kind: 'expense',
      category: 'moradia',
      description: 'Aluguel',
      amount: 2150,
      due_on: diaDoAnterior(5),
      paid_on: diaDoAnterior(5),
    });
    await lancar(page, uid, {
      kind: 'expense',
      category: 'mercado',
      description: 'Feira da semana',
      amount: 804.15,
      due_on: diaDoAnterior(14),
      paid_on: diaDoAnterior(14),
    });

    await page.goto('/mes/repetir');
    await page.waitForLoadState('networkidle');

    const aluguel = page.getByRole('checkbox', { name: 'Copiar Aluguel' });
    const feira = page.getByRole('checkbox', { name: 'Copiar Feira da semana' });

    await expect(aluguel).toBeChecked();
    await expect(
      feira,
      'copiar gasto variável inventaria despesa: o valor do mês que passou é fato daquele mês'
    ).not.toBeChecked();

    await page.getByRole('button', { name: /Copiar 1 lançamento/ }).click();

    await expect(page).toHaveURL(/\/mes/);
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/^A vencer · \d+$/)).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Aluguel' }).first()).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Feira da semana' })).toHaveCount(0);
  });

  test('o que já está no mês de destino não é oferecido de novo', async ({ page }) => {
    const uid = titular('molde_sem_duplicar');
    await entrarComo(page, uid);

    await lancar(page, uid, {
      kind: 'expense',
      category: 'moradia',
      description: 'Aluguel',
      amount: 2150,
      due_on: diaDoAnterior(5),
      paid_on: diaDoAnterior(5),
    });
    await lancar(page, uid, {
      kind: 'expense',
      category: 'moradia',
      description: 'Aluguel',
      amount: 2250,
      due_on: dia(5),
      paid_on: dia(5),
    });

    await page.goto('/mes/repetir');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('já está lá')).toBeVisible();
    await expect(page.getByRole('checkbox', { name: 'Copiar Aluguel' })).toBeDisabled();
  });

  test('sem mês anterior lançado, a tela diz isso em vez de abrir vazia', async ({ page }) => {
    const uid = titular('molde_vazio');
    await entrarComo(page, uid);
    await page.goto('/mes/repetir');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/não tem nada lançado/)).toBeVisible();
    await expect(page.getByRole('link', { name: /Lançar/ }).first()).toBeVisible();
  });
});
