import { HttpErrorResponse } from '@angular/common/http';
import { TimeoutError } from 'rxjs';

/**
 * A frase que a pessoa lê quando algo não carregou — uma só, para o produto inteiro.
 *
 * `acao` completa "Não conseguimos ___ agora": passe o verbo no infinitivo com o objeto
 * ("carregar suas posições"), não o nome da rota.
 */
export function mensagemDeErro(erro: unknown, acao?: string): string {
  const oQue = acao ?? 'carregar estes dados';

  if (erro instanceof TimeoutError) {
    return 'A resposta demorou demais. Sua conexão pode estar instável.';
  }

  if (typeof erro === 'string' && erro.trim()) return erro;

  if (erro instanceof HttpErrorResponse) {
    // Status 0 é rede, não servidor: pedir para a pessoa "conferir se o backend está rodando"
    // era mensagem de quem desenvolve, entregue a quem usa.
    if (erro.status === 0) {
      return 'Sem conexão com a internet. Seus dados salvos continuam intactos.';
    }
    if (erro.status === 401 || erro.status === 403) {
      return 'Sua sessão expirou. Entre novamente para continuar.';
    }
    if (erro.status === 404) {
      return 'Não encontramos o que você pediu.';
    }
    if (erro.status === 429) {
      return 'Você fez muitos pedidos em pouco tempo. Aguarde um minuto e tente de novo.';
    }
    if (erro.status === 422) {
      return 'Alguns dados não foram aceitos. Confira os campos e envie de novo.';
    }
    if (erro.status >= 500) {
      return 'O serviço está instável no momento. Tente de novo em instantes.';
    }
  }

  return `Não conseguimos ${oQue} agora. Pode ser a conexão ou uma instabilidade na fonte de cotações.`;
}

/**
 * O texto que o servidor mandou, quando ele fala com a pessoa e não com quem desenvolve.
 *
 * `detail` de 4xx de domínio é escrito para ser lido ("Quantidade acima da posição"); o de 5xx
 * é rastreamento. Só o primeiro sai na tela.
 */
export function detalheUtil(erro: unknown): string | null {
  if (!(erro instanceof HttpErrorResponse)) return null;
  if (erro.status >= 500 || erro.status === 0) return null;

  const detail = (erro.error as { detail?: unknown } | null)?.detail;
  return typeof detail === 'string' && detail.trim() ? detail : null;
}
