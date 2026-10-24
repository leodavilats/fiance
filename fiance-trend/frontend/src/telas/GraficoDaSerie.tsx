import { useMemo, useState, type ReactNode } from "react";
import {
  Brush,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CategoricalChartState } from "recharts/types/chart/types";
import { formatarData, formatarNumero, formatarPorcento } from "../formato";
import {
  amostrar,
  dentro,
  indicesDaJanela,
  paraOGrafico,
  PERIODOS,
  recortar,
  variacao,
  type Janela,
  type Ponto,
  type PontoDoGrafico,
} from "../serie";

const PONTOS_NA_TELA = 800;
const PONTOS_NO_NAVEGADOR = 500;

type Marca = { cx?: number; cy?: number; payload?: PontoDoGrafico; key?: string };

function marcaDeSalto({ cx, cy, payload, key }: Marca) {
  if (!payload?.salto || cx === undefined || cy === undefined) return <g key={key} />;
  return <circle key={key} cx={cx} cy={cy} r={3.5} fill="var(--perde)" stroke="none" />;
}

function Variacao({ rotulo, valor }: { rotulo: string; valor: number | null }) {
  const classe = valor === null ? "" : valor < 0 ? "perde" : "ganha";
  return (
    <span>
      {rotulo} <strong className={classe}>{formatarPorcento(valor)}</strong>
    </span>
  );
}

type Assunto = "escala" | "retorno" | "preco" | "zoom";

function Informativo({
  assunto,
  aberto,
  alternar,
  rotulo,
}: {
  assunto: Assunto;
  aberto: Assunto | null;
  alternar: (a: Assunto) => void;
  rotulo: string;
}) {
  return (
    <button
      type="button"
      className={`informativo${aberto === assunto ? " aberto" : ""}`}
      aria-expanded={aberto === assunto}
      aria-label={rotulo}
      title={rotulo}
      onClick={() => alternar(assunto)}
    >
      ?
    </button>
  );
}

function Explicacao({ visivel, children }: { visivel: boolean; children: ReactNode }) {
  if (!visivel) return null;
  return <div className="explicacao">{children}</div>;
}

export default function GraficoDaSerie({ serie }: { serie: Ponto[] }) {
  const [meses, setMeses] = useState<number | null>(null);
  const [log, setLog] = useState(true);
  const [janela, setJanela] = useState<Janela | null>(null);
  const [selecao, setSelecao] = useState<Janela | null>(null);
  const [aberto, setAberto] = useState<Assunto | null>(null);

  const periodo = useMemo(() => recortar(serie, meses), [serie, meses]);
  const navegador = useMemo(() => paraOGrafico(amostrar(periodo, PONTOS_NO_NAVEGADOR)), [periodo]);
  const visivel = useMemo(() => paraOGrafico(amostrar(dentro(periodo, janela), PONTOS_NA_TELA)), [periodo, janela]);

  if (visivel.length === 0) return <p className="nota">Sem pregões na base.</p>;

  const alternar = (a: Assunto) => setAberto(aberto === a ? null : a);
  const primeiro = visivel[0].data;
  const ultimo = visivel[visivel.length - 1].data;
  const dias = (Date.parse(ultimo) - Date.parse(primeiro)) / 86_400_000;
  const marcaDoEixo = (v: string) => (dias > 730 ? v.slice(0, 4) : `${v.slice(5, 7)}/${v.slice(2, 4)}`);
  const escala = log ? "log" : "linear";
  const temPreco = visivel.some((p) => p.preco !== null);
  const saltos = visivel.filter((p) => p.salto).length;
  const [inicioDaFaixa, fimDaFaixa] = indicesDaJanela(navegador, janela);

  const soltar = () => {
    if (selecao && selecao[0] !== selecao[1]) {
      setJanela(selecao[0] < selecao[1] ? selecao : [selecao[1], selecao[0]]);
    }
    setSelecao(null);
  };
  const arraste = {
    onMouseDown: (e: CategoricalChartState) => e?.activeLabel && setSelecao([e.activeLabel, e.activeLabel]),
    onMouseMove: (e: CategoricalChartState) => selecao && e?.activeLabel && setSelecao([selecao[0], e.activeLabel]),
    onMouseUp: soltar,
    onMouseLeave: soltar,
  };
  const areaSelecionada = selecao && selecao[0] !== selecao[1] && (
    <ReferenceArea x1={selecao[0]} x2={selecao[1]} fill="var(--destaque)" fillOpacity={0.12} stroke="none" />
  );

  const eixoX = (
    <XAxis dataKey="data" tickFormatter={marcaDoEixo} minTickGap={40} stroke="var(--suave)" />
  );

  return (
    <>
      <div className="controles">
        <div className="abas">
          {PERIODOS.map((p) => (
            <button
              key={p.rotulo}
              className={meses === p.meses ? "ativa" : ""}
              onClick={() => {
                setMeses(p.meses);
                setJanela(null);
              }}
            >
              {p.rotulo}
            </button>
          ))}
        </div>
        <div className="abas">
          <button className={log ? "ativa" : ""} onClick={() => setLog(true)}>
            Escala log
          </button>
          <button className={log ? "" : "ativa"} onClick={() => setLog(false)}>
            Linear
          </button>
        </div>
        <Informativo assunto="escala" aberto={aberto} alternar={alternar} rotulo="O que muda entre log e linear" />
      </div>
      <Explicacao visivel={aberto === "escala"}>
        <p>
          <strong>Escala log:</strong> a mesma distância no eixo vale a mesma variação percentual — ir de R$ 10 a R$ 20
          ocupa o mesmo espaço que ir de R$ 100 a R$ 200, porque os dois dobraram. É a escala para comparar épocas
          diferentes: a inclinação da linha é a velocidade do ganho, em qualquer ponto.
        </p>
        <p>
          <strong>Linear:</strong> a mesma distância vale o mesmo valor absoluto. Mostra o preço como ele é, mas numa
          janela longa os movimentos recentes, com o preço mais alto, parecem maiores do que foram, e os antigos
          ficam achatados no fundo.
        </p>
      </Explicacao>

      <p className="nota">
        {formatarData(primeiro)} a {formatarData(ultimo)} · <Variacao rotulo="retorno total" valor={variacao(visivel, "retorno")} />
        {temPreco && (
          <>
            {" "}
            · <Variacao rotulo="preço" valor={variacao(visivel, "preco")} />
          </>
        )}
      </p>

      {navegador.length > 2 && (
        <>
          <div className="controles">
            <h3>
              Navegador{" "}
              <Informativo assunto="zoom" aberto={aberto} alternar={alternar} rotulo="Como aproximar um trecho" />
            </h3>
            {janela && (
              <div className="abas">
                <button onClick={() => setJanela(null)}>Desfazer zoom</button>
              </div>
            )}
          </div>
          <Explicacao visivel={aberto === "zoom"}>
            <p>
              Clique e arraste sobre qualquer um dos gráficos para aproximar o trecho marcado. Na faixa abaixo, puxe as
              bordas para mudar o começo e o fim, ou arraste o meio para deslizar a janela sem mudar a largura.{" "}
              <strong>Desfazer zoom</strong> volta ao período inteiro; trocar o período também.
            </p>
          </Explicacao>
          <div className="grafico navegador">
            <ResponsiveContainer>
              <LineChart data={navegador} margin={{ top: 0, right: 8, bottom: 0, left: 8 }}>
                <Brush
                  dataKey="data"
                  height={52}
                  stroke="var(--suave)"
                  fill="var(--superficie)"
                  travellerWidth={10}
                  tickFormatter={(v: string) => formatarData(v)}
                  startIndex={inicioDaFaixa}
                  endIndex={fimDaFaixa}
                  onChange={({ startIndex, endIndex }) => {
                    if (startIndex === undefined || endIndex === undefined) return;
                    const inteira = startIndex === 0 && endIndex === navegador.length - 1;
                    setJanela(inteira ? null : [navegador[startIndex].data, navegador[endIndex].data]);
                  }}
                >
                  <LineChart>
                    <Line dataKey="retorno" dot={false} stroke="var(--suave)" isAnimationActive={false} />
                  </LineChart>
                </Brush>
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      <h3>
        Retorno total, base 100{" "}
        <Informativo assunto="retorno" aberto={aberto} alternar={alternar} rotulo="O que é o retorno total" />
      </h3>
      <Explicacao visivel={aberto === "retorno"}>
        <p>
          Quanto viraram R$ 100 aplicados no primeiro dia da janela, com cada provento reinvestido no próprio papel na
          data ex e o preço ajustado por desdobramento, grupamento e bonificação. É o ganho de quem comprou e segurou —
          a medida para comparar ativos. Recomeça em 100 a cada período ou zoom: 150 no fim quer dizer +50% na janela.
        </p>
        <p>Dia com salto sem evento fica fora da conta, para um evento que faltou na base não virar ganho ou perda.</p>
      </Explicacao>
      <div className="grafico zoom">
        <ResponsiveContainer>
          <LineChart data={visivel} syncId="serie" syncMethod="value" {...arraste}>
            <CartesianGrid stroke="var(--fio)" vertical={false} />
            {eixoX}
            <YAxis
              scale={escala}
              domain={["auto", "auto"]}
              stroke="var(--suave)"
              tickFormatter={(v: number) => formatarNumero(v)}
            />
            <Tooltip formatter={(v: number) => formatarNumero(v)} labelFormatter={(v: string) => formatarData(v)} />
            <Line
              dataKey="retorno"
              name="retorno total"
              dot={false}
              stroke="var(--destaque)"
              strokeWidth={2}
              isAnimationActive={false}
            />
            {areaSelecionada}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h3>
        Preço de fechamento, R$ sem ajuste{" "}
        <Informativo assunto="preco" aberto={aberto} alternar={alternar} rotulo="Por que o preço difere do retorno" />
      </h3>
      <Explicacao visivel={aberto === "preco"}>
        <p>
          O preço negociado no fim de cada pregão, como saiu na B3, sem nenhum ajuste. Ele cai na data ex de cada
          provento e muda de patamar num desdobramento ou grupamento — por isso a variação do preço pode ficar bem
          abaixo do retorno total, principalmente em quem paga muito provento.
        </p>
        <p>
          <span className="perde">●</span> marca um <strong>salto sem evento</strong>: o preço variou mais de 50%, ou
          numa razão típica de desdobramento, e não há evento na base que explique. Em geral é um evento que a B3 não
          publicou; às vezes é movimento real.
        </p>
      </Explicacao>
      {!temPreco ? (
        <p className="nota">Sem preço de fechamento nesta janela.</p>
      ) : (
        <>
          {saltos > 0 && (
            <p className="nota">
              <span className="perde">●</span> {saltos} dia(s) com salto sem evento nesta janela.
            </p>
          )}
          <div className="grafico zoom">
            <ResponsiveContainer>
              <LineChart data={visivel} syncId="serie" syncMethod="value" {...arraste}>
                <CartesianGrid stroke="var(--fio)" vertical={false} />
                {eixoX}
                <YAxis
                  scale={escala}
                  domain={["auto", "auto"]}
                  stroke="var(--suave)"
                  tickFormatter={(v: number) => formatarNumero(v)}
                />
                <Tooltip
                  formatter={(v: number) => `R$ ${formatarNumero(v)}`}
                  labelFormatter={(v: string) => formatarData(v)}
                />
                <Line
                  dataKey="preco"
                  name="fechamento"
                  dot={marcaDeSalto}
                  activeDot={{ r: 4 }}
                  stroke="var(--referencia)"
                  strokeWidth={2}
                  isAnimationActive={false}
                />
                {areaSelecionada}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </>
  );
}
