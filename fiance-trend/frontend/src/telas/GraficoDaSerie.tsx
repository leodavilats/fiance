import { useMemo, useState } from "react";
import { Brush, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatarData, formatarNumero, formatarPorcento } from "../formato";
import { amostrar, paraOGrafico, PERIODOS, recortar, variacao, type Ponto, type PontoDoGrafico } from "../serie";

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

export default function GraficoDaSerie({ serie }: { serie: Ponto[] }) {
  const [meses, setMeses] = useState<number | null>(null);
  const [log, setLog] = useState(true);
  const [janela, setJanela] = useState<[number, number] | null>(null);

  const periodo = useMemo(() => recortar(serie, meses), [serie, meses]);
  const navegador = useMemo(() => amostrar(periodo, PONTOS_NO_NAVEGADOR), [periodo]);
  const visivel = useMemo(() => {
    const de = janela ? navegador[janela[0]]?.data : undefined;
    const ate = janela ? navegador[janela[1]]?.data : undefined;
    const recorte = de && ate ? periodo.filter((p) => p.data >= de && p.data <= ate) : periodo;
    return paraOGrafico(amostrar(recorte, PONTOS_NA_TELA));
  }, [periodo, navegador, janela]);

  if (visivel.length === 0) return <p className="nota">Sem pregões na base.</p>;

  const primeiro = visivel[0].data;
  const ultimo = visivel[visivel.length - 1].data;
  const dias = (Date.parse(ultimo) - Date.parse(primeiro)) / 86_400_000;
  const marcaDoEixo = (v: string) => (dias > 730 ? v.slice(0, 4) : `${v.slice(5, 7)}/${v.slice(2, 4)}`);
  const escala = log ? "log" : "linear";
  const temPreco = visivel.some((p) => p.preco !== null);
  const saltos = visivel.filter((p) => p.salto).length;

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
        {janela && (
          <div className="abas">
            <button onClick={() => setJanela(null)}>Desfazer zoom</button>
          </div>
        )}
      </div>

      <p className="nota">
        {formatarData(primeiro)} a {formatarData(ultimo)} · <Variacao rotulo="retorno total" valor={variacao(visivel, "retorno")} />
        {temPreco && (
          <>
            {" "}
            · <Variacao rotulo="preço" valor={variacao(visivel, "preco")} />
          </>
        )}
      </p>

      <h3>Retorno total (base 100 no início da janela)</h3>
      <div className="grafico">
        <ResponsiveContainer>
          <LineChart data={visivel} syncId="serie" syncMethod="value">
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
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h3>Preço de fechamento (R$, sem ajuste)</h3>
      {!temPreco ? (
        <p className="nota">Sem preço de fechamento nesta janela.</p>
      ) : (
        <>
          {saltos > 0 && (
            <p className="nota">
              <span className="perde">●</span> {saltos} dia(s) com salto sem evento nesta janela.
            </p>
          )}
          <div className="grafico">
            <ResponsiveContainer>
              <LineChart data={visivel} syncId="serie" syncMethod="value">
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
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {navegador.length > 2 && (
        <>
          <p className="nota">Arraste as bordas da faixa abaixo para aproximar uma parte do período.</p>
          <div className="grafico navegador">
            <ResponsiveContainer>
              <LineChart data={paraOGrafico(navegador)} margin={{ top: 0, right: 8, bottom: 0, left: 8 }}>
                <Brush
                  key={String(meses)}
                  dataKey="data"
                  height={52}
                  stroke="var(--suave)"
                  fill="var(--superficie)"
                  travellerWidth={10}
                  tickFormatter={(v: string) => formatarData(v)}
                  startIndex={janela?.[0]}
                  endIndex={janela?.[1]}
                  onChange={({ startIndex, endIndex }) => {
                    if (startIndex === undefined || endIndex === undefined) return;
                    setJanela(startIndex === 0 && endIndex === navegador.length - 1 ? null : [startIndex, endIndex]);
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
    </>
  );
}
