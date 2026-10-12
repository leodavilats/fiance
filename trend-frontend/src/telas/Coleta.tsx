import { useApi } from "../api";
import { formatarData, formatarNumero } from "../formato";
import Estado from "./Estado";

type DadosDaColeta = {
  ultimas: {
    fonte: string;
    arquivo: string;
    status: string;
    iniciada_em: string;
    linhas_gravadas: number | null;
    linhas_quarentena: number | null;
    erro: string | null;
  }[];
  falhas_7_dias: { fonte: string; falhas: number; ultima: string }[];
  quarentena: { motivo: string; linhas: number }[];
  atualidade: { base: string; ate: string | null }[];
};

export default function TelaColeta() {
  const estado = useApi<DadosDaColeta>("/api/coleta");
  return (
    <>
      <h1>Coleta</h1>
      <p className="nota">O data-job roda às 23h de Brasília depois de cada pregão.</p>
      <Estado estado={estado}>
        {(dados) => (
          <>
            <h2>Até onde cada base vai</h2>
            <div className="rolar">
              <table>
                <tbody>
                  {dados.atualidade.map((a) => (
                    <tr key={a.base}>
                      <td className="esq">{a.base}</td>
                      <td>{formatarData(a.ate)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h2>Última execução de cada fonte</h2>
            <div className="rolar">
              <table>
                <thead>
                  <tr>
                    <th className="esq">Fonte</th>
                    <th className="esq">Arquivo</th>
                    <th className="esq">Status</th>
                    <th>Quando</th>
                    <th>Gravadas</th>
                    <th>Quarentena</th>
                  </tr>
                </thead>
                <tbody>
                  {dados.ultimas.map((c) => (
                    <tr key={c.fonte}>
                      <td className="esq">{c.fonte}</td>
                      <td className="esq">{c.arquivo}</td>
                      <td className={`esq ${c.status === "falhou" ? "perde" : ""}`} title={c.erro ?? ""}>
                        {c.status}
                      </td>
                      <td>{formatarData(c.iniciada_em)}</td>
                      <td>{formatarNumero(c.linhas_gravadas)}</td>
                      <td>{formatarNumero(c.linhas_quarentena)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h2>Falhas nos últimos 7 dias</h2>
            {dados.falhas_7_dias.length === 0 ? (
              <p className="nota">Nenhuma.</p>
            ) : (
              <div className="rolar">
                <table>
                  <tbody>
                    {dados.falhas_7_dias.map((f) => (
                      <tr key={f.fonte}>
                        <td className="esq perde">{f.fonte}</td>
                        <td>{f.falhas}</td>
                        <td>{formatarData(f.ultima)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <h2>Quarentena</h2>
            <div className="rolar">
              <table>
                <tbody>
                  {dados.quarentena.map((q) => (
                    <tr key={q.motivo}>
                      <td className="esq">{q.motivo}</td>
                      <td>{formatarNumero(q.linhas)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Estado>
    </>
  );
}
