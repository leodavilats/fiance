import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  FormArray,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import {
  LoadingService,
  PortfolioItem,
  PortfolioEvaluationResponse,
  PortfolioCategory,
  RecommendService,
  RendaFixaTipo,
  UiHelperService,
} from '../../core';

interface PortfolioItemForm {
  ticker: FormControl<string>;
  quantity: FormControl<number>;
  avg_price: FormControl<number>;
  category: FormControl<PortfolioCategory>;
}

interface RendaFixaItemForm {
  nome: FormControl<string>;
  tipo: FormControl<RendaFixaTipo>;
  valor_investido: FormControl<number>;
  taxa: FormControl<number>;
  prazo_meses: FormControl<number>;
  data_aplicacao: FormControl<string>;
  tipo_taxa: FormControl<'pre_fixado' | 'pos_fixado' | 'hibrido'>;
  percentual_cdi: FormControl<number | null>;
}

interface PortfolioFormShape {
  items: FormArray<FormGroup<PortfolioItemForm>>;
  renda_fixa: FormArray<FormGroup<RendaFixaItemForm>>;
  desired_yield: FormControl<number>;
}

@Component({
  selector: 'app-assets',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <!-- Resumo Consolidado -->
    <div
      class="p-6 rounded-lg bg-gradient-to-br from-accent/10 to-accent/5 border border-accent/20 mb-5"
    >
      <h2 class="flex items-center gap-2 text-2xl font-bold m-0 mb-4 text-tx">
        <lucide-icon name="wallet" size="24"></lucide-icon> Resumo Geral
      </h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="p-4 rounded-lg bg-panel border border-border">
          <div class="text-xs text-muted mb-1 uppercase tracking-wide">Total Investido</div>
          <div class="text-2xl font-bold text-tx">R$ {{ totalInvestido() | number: '1.2-2' }}</div>
          <div class="text-xs text-muted mt-1">Todos os ativos</div>
        </div>
        <div class="p-4 rounded-lg bg-panel border border-border">
          <div class="text-xs text-muted mb-1 uppercase tracking-wide">Valor Atual</div>
          <div class="text-2xl font-bold text-tx">R$ {{ valorAtual() | number: '1.2-2' }}</div>
          <div class="text-xs text-muted mt-1">
            @if (result()) {
              Cotação atualizada
            } @else {
              Clique em "Avaliar" para atualizar
            }
          </div>
        </div>
        <div
          class="p-4 rounded-lg bg-panel border border-border"
          [class.good]="rendimentoTotal() >= 0"
          [class.warn]="rendimentoTotal() < 0"
        >
          <div class="text-xs text-muted mb-1 uppercase tracking-wide">Rendimento</div>
          <div class="text-2xl font-bold text-tx">
            {{ rendimentoTotal() >= 0 ? '+' : '' }}R$ {{ rendimentoTotal() | number: '1.2-2' }}
          </div>
          <div class="text-xs mt-1">
            {{ rendimentoPct() >= 0 ? '+' : '' }}{{ rendimentoPct() | number: '1.2-2' }}%
          </div>
        </div>
        <div class="p-4 rounded-lg bg-panel border border-border">
          <div class="text-xs text-muted mb-1 uppercase tracking-wide">Ativos</div>
          <div class="text-2xl font-bold text-tx">{{ totalAtivos() }}</div>
          <div class="text-xs text-muted mt-1">
            {{ portfolioItems.length }} negociados + {{ rendaFixaItems.length }} RF
          </div>
        </div>
      </div>
    </div>

    <!-- Ativos Negociados -->
    <div class="p-5 rounded-lg bg-panel border border-border mb-5">
      <div class="flex items-center justify-between mb-4">
        <h2 class="flex items-center gap-2 text-xl font-bold m-0 text-tx">
          <lucide-icon name="trending-up" size="20"></lucide-icon> Ativos Negociados
          <span class="text-base font-normal text-muted ml-2">({{ portfolioItems.length }})</span>
        </h2>
        <button
          type="button"
          class="text-sm text-muted hover:text-tx transition-colors cursor-pointer flex items-center gap-1"
          (click)="toggleSection('negociados')"
        >
          <lucide-icon
            [name]="expandedSections.negociados ? 'chevron-up' : 'chevron-down'"
            size="16"
          ></lucide-icon>
          {{ expandedSections.negociados ? 'Recolher' : 'Expandir' }}
        </button>
      </div>

      @if (expandedSections.negociados) {
        <p class="text-sm text-muted mb-4">
          Ações, FIIs, criptomoedas e outros ativos com ticker/cotação em bolsa.
        </p>

        <form [formGroup]="form">
          <div
            class="grid grid-cols-[2fr_1fr_1fr_1.5fr_auto] gap-2 mb-2 text-sm font-medium text-muted"
          >
            <div>Ticker</div>
            <div>Quantidade</div>
            <div>Preço médio</div>
            <div>Categoria</div>
            <div></div>
          </div>
          <div class="flex flex-col gap-2" formArrayName="items">
            @for (item of portfolioItems.controls; track $index; let i = $index) {
              <div
                class="grid grid-cols-[2fr_1fr_1fr_1.5fr_auto] gap-2 items-center"
                [formGroupName]="i"
              >
                <input
                  type="text"
                  formControlName="ticker"
                  placeholder="ex.: PETR4"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                />
                <input
                  type="number"
                  formControlName="quantity"
                  placeholder="qtd"
                  step="0.0001"
                  min="0"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                />
                <input
                  type="number"
                  formControlName="avg_price"
                  placeholder="preço"
                  step="0.01"
                  min="0"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                />
                <select
                  formControlName="category"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box; background-image: url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2712%27 height=%2712%27 viewBox=%270 0 12 12%27%3E%3Cpath fill=%27%239ba3b4%27 d=%27M6 8L2 4h8z%27/%3E%3C/svg%3E'); background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px;"
                >
                  <option value="auto">Auto</option>
                  <option value="renda">Renda</option>
                  <option value="trade">Trade</option>
                </select>
                <button
                  type="button"
                  class="w-9 h-9 grid place-items-center rounded-lg cursor-pointer bg-panel-2 border border-border text-danger hover:bg-danger hover:text-white transition-colors"
                  (click)="removeItem(i)"
                  title="Remover"
                >
                  <lucide-icon name="x" size="16"></lucide-icon>
                </button>
              </div>
            }
          </div>
          @if (portfolioItems.length === 0) {
            <div
              class="text-center py-8 text-muted text-sm bg-bg-2 rounded-lg border border-dashed border-border"
            >
              <lucide-icon name="inbox" size="32" class="mx-auto mb-2 opacity-50"></lucide-icon>
              <p>Nenhum ativo negociado cadastrado.</p>
              <p class="text-xs mt-1">Clique em "Adicionar ativo" para começar.</p>
            </div>
          }
          <div class="flex items-center gap-3 mt-4 flex-wrap">
            <button
              type="button"
              class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all"
              (click)="addItem()"
            >
              <lucide-icon name="plus" size="16"></lucide-icon> Adicionar ativo
            </button>
            <button
              type="button"
              class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
              (click)="evaluateAssets()"
              [disabled]="loading.loading() || portfolioItems.length === 0"
            >
              <lucide-icon
                [name]="loading.loading() ? 'loader-circle' : 'refresh-cw'"
                [class.animate-spin]="loading.loading()"
                size="16"
              ></lucide-icon>
              {{ loading.loading() ? 'Avaliando...' : 'Avaliar agora' }}
            </button>
          </div>
        </form>
      }
    </div>

    <!-- Renda Fixa -->
    <div class="p-5 rounded-lg bg-panel border border-border mb-5">
      <div class="flex items-center justify-between mb-4">
        <h2 class="flex items-center gap-2 text-xl font-bold m-0 text-tx">
          <lucide-icon name="landmark" size="20"></lucide-icon> Renda Fixa
          <span class="text-base font-normal text-muted ml-2">({{ rendaFixaItems.length }})</span>
        </h2>
        <button
          type="button"
          class="text-sm text-muted hover:text-tx transition-colors cursor-pointer flex items-center gap-1"
          (click)="toggleSection('rendaFixa')"
        >
          <lucide-icon
            [name]="expandedSections.rendaFixa ? 'chevron-up' : 'chevron-down'"
            size="16"
          ></lucide-icon>
          {{ expandedSections.rendaFixa ? 'Recolher' : 'Expandir' }}
        </button>
      </div>

      <!-- Resumo Renda Fixa (sempre visível) -->
      @if (rendaFixaItems.length > 0) {
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
          <div class="p-3 rounded-lg bg-bg-2 border border-border">
            <div class="text-xs text-muted mb-1 uppercase tracking-wide">Investido</div>
            <div class="text-lg font-bold text-tx">R$ {{ totalRendaFixa() | number: '1.2-2' }}</div>
          </div>
          <div class="p-3 rounded-lg bg-bg-2 border border-border good">
            <div class="text-xs text-muted mb-1 uppercase tracking-wide">Rendimento Atual</div>
            <div class="text-lg font-bold">+R$ {{ totalRendimentoRF() | number: '1.2-2' }}</div>
            <div class="text-xs text-muted mt-1">Proporcional</div>
          </div>
          <div class="p-3 rounded-lg bg-bg-2 border border-border">
            <div class="text-xs text-muted mb-1 uppercase tracking-wide">Valor Atual</div>
            <div class="text-lg font-bold text-tx">
              R$ {{ totalValorAtualRF() | number: '1.2-2' }}
            </div>
            <div class="text-xs text-muted mt-1">Hoje</div>
          </div>
          <div class="p-3 rounded-lg bg-bg-2 border border-border">
            <div class="text-xs text-muted mb-1 uppercase tracking-wide">Valor Futuro</div>
            <div class="text-lg font-bold text-tx">
              R$ {{ totalValorFuturoRF() | number: '1.2-2' }}
            </div>
            <div class="text-xs text-muted mt-1">No vencimento</div>
          </div>
          <div class="p-3 rounded-lg bg-bg-2 border border-border">
            <div class="text-xs text-muted mb-1 uppercase tracking-wide">Taxa Média</div>
            <div class="text-lg font-bold text-tx">{{ avgTaxaRF() | number: '1.2-2' }}% a.a.</div>
          </div>
        </div>
      }

      @if (expandedSections.rendaFixa) {
        <p class="text-sm text-muted mb-4">
          CDB, LCI, LCA, Tesouro Direto e outros títulos de renda fixa.
        </p>

        <div class="p-3 rounded-lg bg-info/5 border border-info/20 mb-4 text-xs text-muted">
          <div class="flex items-start gap-2">
            <lucide-icon name="info" size="14" class="mt-0.5 flex-shrink-0 text-info"></lucide-icon>
            <div>
              <strong class="text-tx">Cálculo de rendimentos:</strong> O rendimento atual é
              proporcional ao tempo decorrido desde a aplicação. O valor futuro mostra o esperado no
              vencimento. <br /><br />
              <strong class="text-tx">IR:</strong> Todos os valores são líquidos (já descontados o
              IR). Alíquotas: 22,5% (até 180d), 20% (181-360d), 17,5% (361-720d), 15% (>720d).
              <strong class="text-tx">LCI, LCA, CRI e CRA são isentos</strong> de imposto de renda.
            </div>
          </div>
        </div>

        <form [formGroup]="form">
          <div
            class="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_1fr_1.2fr_auto] gap-2 mb-2 text-sm font-medium text-muted"
          >
            <div>Nome/Banco</div>
            <div>Tipo</div>
            <div>Tipo Taxa</div>
            <div>Valor (R$)</div>
            <div>Taxa/% CDI</div>
            <div>Prazo (m)</div>
            <div>Aplicação</div>
            <div></div>
          </div>
          <div class="flex flex-col gap-2" formArrayName="renda_fixa">
            @for (rf of rendaFixaItems.controls; track $index; let i = $index) {
              <div
                class="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_1fr_1.2fr_auto] gap-2 items-start"
                [formGroupName]="i"
              >
                <input
                  type="text"
                  formControlName="nome"
                  placeholder="ex.: Banco Inter"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                />
                <select
                  formControlName="tipo"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box; background-image: url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2712%27 height=%2712%27 viewBox=%270 0 12 12%27%3E%3Cpath fill=%27%239ba3b4%27 d=%27M6 8L2 4h8z%27/%3E%3C/svg%3E'); background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px;"
                >
                  <option value="cdb">CDB</option>
                  <option value="lci">LCI</option>
                  <option value="lca">LCA</option>
                  <option value="tesouro_selic">Tesouro Selic</option>
                  <option value="tesouro_ipca">Tesouro IPCA+</option>
                  <option value="tesouro_pre">Tesouro Pré</option>
                  <option value="lc">LC</option>
                  <option value="cri">CRI</option>
                  <option value="cra">CRA</option>
                </select>
                <select
                  formControlName="tipo_taxa"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box; background-image: url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2712%27 height=%2712%27 viewBox=%270 0 12 12%27%3E%3Cpath fill=%27%239ba3b4%27 d=%27M6 8L2 4h8z%27/%3E%3C/svg%3E'); background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px;"
                >
                  <option value="pre_fixado">Pré</option>
                  <option value="pos_fixado">Pós (CDI)</option>
                  <option value="hibrido">Híbrido</option>
                </select>
                <input
                  type="number"
                  formControlName="valor_investido"
                  placeholder="10000"
                  min="0"
                  step="100"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                />
                @if (rf.controls.tipo_taxa.value === 'pos_fixado') {
                  <input
                    type="number"
                    formControlName="percentual_cdi"
                    placeholder="110"
                    min="0"
                    step="1"
                    class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                  />
                } @else {
                  <input
                    type="number"
                    formControlName="taxa"
                    placeholder="12.5"
                    min="0"
                    step="0.1"
                    class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                  />
                }
                <input
                  type="number"
                  formControlName="prazo_meses"
                  placeholder="12"
                  min="1"
                  step="1"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                />
                <input
                  type="date"
                  formControlName="data_aplicacao"
                  class="px-3 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  style="height: 42px; appearance: none; -webkit-appearance: none; -moz-appearance: none; box-sizing: border-box;"
                />
                <button
                  type="button"
                  class="w-9 h-9 grid place-items-center rounded-lg cursor-pointer bg-panel-2 border border-border text-danger hover:bg-danger hover:text-white transition-colors"
                  (click)="removeRF(i)"
                  title="Remover"
                >
                  <lucide-icon name="x" size="16"></lucide-icon>
                </button>
              </div>
            }
          </div>
          @if (rendaFixaItems.length === 0) {
            <div
              class="text-center py-8 text-muted text-sm bg-bg-2 rounded-lg border border-dashed border-border"
            >
              <lucide-icon name="landmark" size="32" class="mx-auto mb-2 opacity-50"></lucide-icon>
              <p>Nenhum ativo de renda fixa cadastrado.</p>
              <p class="text-xs mt-1">Clique em "Adicionar RF" para começar.</p>
            </div>
          }
          <div class="flex items-center gap-3 mt-4 flex-wrap">
            <button
              type="button"
              class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all"
              (click)="addRF()"
            >
              <lucide-icon name="plus" size="16"></lucide-icon> Adicionar RF
            </button>
          </div>
        </form>
      }
    </div>

    <!-- Detalhamento Renda Fixa -->
    @if (rendaFixaItems.length > 0 && expandedSections.rendaFixa) {
      <div class="p-5 rounded-lg bg-panel border border-border mb-5">
        <h3 class="text-lg font-bold m-0 mb-4 text-tx">Detalhamento - Renda Fixa</h3>
        <div style="overflow-x:auto;">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-border">
                <th class="text-left py-2 px-2 font-medium text-muted">Nome</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Tipo</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Investido</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Taxa</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Prazo</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Rend. Atual</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Valor no Vencimento</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Aplicação</th>
              </tr>
            </thead>
            <tbody>
              @for (rf of rendaFixaItems.controls; track $index; let i = $index) {
                <tr class="border-b border-border hover:bg-bg-2 transition-colors">
                  <td class="py-2 px-2 text-tx font-medium">{{ rf.controls.nome.value }}</td>
                  <td class="py-2 px-2">
                    <div class="flex items-center gap-2">
                      <span class="tag">{{ rfTipoLabel(rf.controls.tipo.value) }}</span>
                      @if (isIsentoIR(rf.controls.tipo.value)) {
                        <span
                          class="text-xs px-2 py-0.5 rounded bg-success/10 text-success border border-success/20"
                          >Isento IR</span
                        >
                      }
                    </div>
                  </td>
                  <td class="text-right py-2 px-2 text-tx">
                    R$ {{ rf.controls.valor_investido.value | number: '1.2-2' }}
                  </td>
                  <td class="text-right py-2 px-2 text-tx">
                    @if (rf.controls.tipo_taxa.value === 'pos_fixado') {
                      {{ rf.controls.percentual_cdi.value }}% CDI
                    } @else {
                      {{ rf.controls.taxa.value }}% a.a.
                    }
                  </td>
                  <td class="text-right py-2 px-2 text-tx">{{ rf.controls.prazo_meses.value }}m</td>
                  <td class="text-right py-2 px-2 good">
                    +R$ {{ calcularRendimento(i) | number: '1.2-2' }}
                  </td>
                  <td class="text-right py-2 px-2 text-tx font-semibold">
                    R$ {{ calcularValorFinal(i) | number: '1.2-2' }}
                  </td>
                  <td class="py-2 px-2 text-muted text-xs">
                    {{ rf.controls.data_aplicacao.value | date: 'dd/MM/yyyy' }}
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    }

    <!-- Resultado da Avaliação - Ativos Negociados -->
    @if (result(); as r) {
      <div class="p-5 rounded-lg bg-panel border border-border mb-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="flex items-center gap-2 text-xl font-bold m-0 text-tx">
            <lucide-icon name="bar-chart-3" size="20"></lucide-icon> Análise - Ativos Negociados
          </h2>
          <button
            type="button"
            class="text-sm text-muted hover:text-tx transition-colors cursor-pointer flex items-center gap-1"
            (click)="toggleSection('avaliacao')"
          >
            <lucide-icon
              [name]="expandedSections.avaliacao ? 'chevron-up' : 'chevron-down'"
              size="16"
            ></lucide-icon>
            {{ expandedSections.avaliacao ? 'Recolher' : 'Expandir' }}
          </button>
        </div>

        @if (expandedSections.avaliacao) {
          <p class="leading-relaxed text-sm text-tx mb-4">
            {{ ui.portfolioSummary(r.positions, r.total_pnl, r.total_pnl_pct) }}
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
            <div class="p-4 rounded-lg bg-bg-2 border border-border info">
              <div class="text-xs text-muted mb-1 uppercase tracking-wide">Investido</div>
              <div class="text-xl font-bold text-tx">
                R$ {{ r.total_invested | number: '1.2-2' }}
              </div>
            </div>
            <div
              class="p-4 rounded-lg bg-bg-2 border border-border"
              [class.good]="r.total_pnl >= 0"
              [class.warn]="r.total_pnl < 0"
            >
              <div class="text-xs text-muted mb-1 uppercase tracking-wide">Valor atual</div>
              <div class="text-xl font-bold text-tx">
                R$ {{ r.total_current | number: '1.2-2' }}
              </div>
            </div>
            <div
              class="p-4 rounded-lg bg-bg-2 border border-border"
              [class.good]="r.total_pnl >= 0"
              [class.warn]="r.total_pnl < 0"
            >
              <div class="text-xs text-muted mb-1 uppercase tracking-wide">Resultado</div>
              <div class="text-xl font-bold text-tx">
                {{ r.total_pnl >= 0 ? '+' : '' }}R$ {{ r.total_pnl | number: '1.2-2' }}
              </div>
              <div class="text-sm mt-1">
                {{ r.total_pnl >= 0 ? '+' : '' }}{{ r.total_pnl_pct | number: '1.2-2' }}%
              </div>
            </div>
          </div>

          <div style="overflow-x:auto;">
            <table class="w-full border-collapse text-sm">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-left py-2 px-2 font-medium text-muted">Ativo</th>
                  <th class="text-left py-2 px-2 font-medium text-muted">Categoria</th>
                  <th class="text-right py-2 px-2 font-medium text-muted">Qtd</th>
                  <th class="text-right py-2 px-2 font-medium text-muted">P. médio</th>
                  <th class="text-right py-2 px-2 font-medium text-muted">P. atual</th>
                  <th class="text-right py-2 px-2 font-medium text-muted">P. justo</th>
                  <th class="text-right py-2 px-2 font-medium text-muted">PnL</th>
                  <th class="text-left py-2 px-2 font-medium text-muted">Decisão</th>
                </tr>
              </thead>
              <tbody>
                @for (p of r.positions; track p.ticker) {
                  <tr class="border-b border-border hover:bg-bg-2 transition-colors">
                    <td class="py-2 px-2">
                      <div class="font-semibold text-tx">{{ p.ticker }}</div>
                      <div class="text-xs text-muted">{{ p.name }}</div>
                    </td>
                    <td class="py-2 px-2">
                      <span class="tag tag-cat" [class]="'cat-' + p.category_resolved">{{
                        ui.categoryLabel(p.category_resolved)
                      }}</span>
                    </td>
                    <td class="text-right py-2 px-2 text-tx">{{ p.quantity }}</td>
                    <td class="text-right py-2 px-2 text-tx">
                      {{ p.avg_price | number: '1.2-2' }}
                    </td>
                    <td class="text-right py-2 px-2 text-tx">
                      {{ p.current_price != null ? (p.current_price | number: '1.2-2') : '—' }}
                    </td>
                    <td class="text-right py-2 px-2 text-tx">
                      {{ p.fair_price != null ? (p.fair_price | number: '1.2-2') : '—' }}
                    </td>
                    <td
                      class="text-right py-2 px-2"
                      [class.good]="(p.pnl_pct || 0) >= 0"
                      [class.warn]="(p.pnl_pct || 0) < 0"
                    >
                      {{ p.pnl_pct != null ? (p.pnl_pct | number: '1.2-2') + '%' : '—' }}
                    </td>
                    <td class="py-2 px-2">
                      <span class="verdict-pill" [class]="ui.verdictClass(p.verdict)">{{
                        p.label
                      }}</span>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      </div>
    }
  `,
  styles: [
    `
      .tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 500;
        background-color: rgb(var(--cat-renda_fixa) / 0.15);
        color: rgb(var(--cat-renda_fixa));
      }

      .good {
        background-color: rgb(var(--color-success) / 0.1);
        border-color: rgb(var(--color-success) / 0.3);
        color: rgb(var(--color-success));
      }

      .warn {
        background-color: rgb(var(--color-danger) / 0.1);
        border-color: rgb(var(--color-danger) / 0.3);
        color: rgb(var(--color-danger));
      }

      .info {
        background-color: rgb(var(--color-info) / 0.1);
        border-color: rgb(var(--color-info) / 0.3);
      }

      @keyframes spin {
        from {
          transform: rotate(0deg);
        }
        to {
          transform: rotate(360deg);
        }
      }

      .animate-spin {
        animation: spin 1s linear infinite;
      }
    `,
  ],
})
export class AssetsComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  result = signal<PortfolioEvaluationResponse | null>(null);
  saveState = signal<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Controle de expansão/colapso de seções
  expandedSections = {
    negociados: true,
    rendaFixa: true,
    avaliacao: true,
  };

  private save$ = new Subject<void>();
  private readonly CDI_ATUAL = 13.65; // CDI atual em % a.a.

  form: FormGroup<PortfolioFormShape> = this.fb.group({
    items: this.fb.array<FormGroup<PortfolioItemForm>>([]),
    renda_fixa: this.fb.array<FormGroup<RendaFixaItemForm>>([]),
    desired_yield: this.fb.control(0.06, {
      nonNullable: true,
      validators: [Validators.min(0.02), Validators.max(0.2)],
    }),
  });

  get portfolioItems() {
    return this.form.controls.items;
  }

  get rendaFixaItems() {
    return this.form.controls.renda_fixa;
  }

  ngOnInit(): void {
    this.loadStoredPortfolio();
    this.loadStoredRendaFixa();

    this.form.valueChanges.subscribe(() => {
      this.save$.next();
    });

    this.save$.pipe(debounceTime(800)).subscribe(() => {
      this.persistPortfolio();
      this.persistRendaFixa();
    });
  }

  addItem(): void {
    const group = this.fb.group<PortfolioItemForm>({
      ticker: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      quantity: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0.0001)],
      }),
      avg_price: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0.0001)],
      }),
      category: this.fb.control<'auto' | 'renda' | 'trade'>('auto', { nonNullable: true }),
    });
    this.portfolioItems.push(group);
  }

  removeItem(i: number): void {
    this.portfolioItems.removeAt(i);
  }

  addRF(): void {
    const group = this.fb.group<RendaFixaItemForm>({
      nome: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      tipo: this.fb.control<RendaFixaTipo>('cdb', { nonNullable: true }),
      valor_investido: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(1)],
      }),
      taxa: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(0)],
      }),
      prazo_meses: this.fb.control(0, {
        nonNullable: true,
        validators: [Validators.required, Validators.min(1)],
      }),
      data_aplicacao: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      tipo_taxa: this.fb.control<'pre_fixado' | 'pos_fixado' | 'hibrido'>('pre_fixado', {
        nonNullable: true,
      }),
      percentual_cdi: this.fb.control<number | null>(null),
    });
    this.rendaFixaItems.push(group);
  }

  removeRF(i: number): void {
    this.rendaFixaItems.removeAt(i);
  }

  toggleSection(section: 'negociados' | 'rendaFixa' | 'avaliacao'): void {
    this.expandedSections[section] = !this.expandedSections[section];
  }

  // Resumo Consolidado
  totalInvestido(): number {
    const negociados = this.portfolioItems.controls.reduce(
      (sum, item) => sum + (item.controls.quantity.value * item.controls.avg_price.value || 0),
      0
    );
    return negociados + this.totalRendaFixa();
  }

  valorAtual(): number {
    const result = this.result();
    const negociados = result ? result.total_current : 0;
    const rf = this.totalValorAtualRF();
    return negociados + rf;
  }

  rendimentoTotal(): number {
    return this.valorAtual() - this.totalInvestido();
  }

  rendimentoPct(): number {
    const investido = this.totalInvestido();
    if (investido === 0) return 0;
    return (this.rendimentoTotal() / investido) * 100;
  }

  totalAtivos(): number {
    return this.portfolioItems.length + this.rendaFixaItems.length;
  }

  // Renda Fixa - Cálculos
  totalRendaFixa(): number {
    return this.rendaFixaItems.controls.reduce(
      (sum, rf) => sum + (rf.controls.valor_investido.value || 0),
      0
    );
  }

  totalRendimentoRF(): number {
    return this.rendaFixaItems.controls.reduce((sum, rf, index) => {
      return sum + this.calcularRendimento(index);
    }, 0);
  }

  totalRendimentoTotalRF(): number {
    return this.rendaFixaItems.controls.reduce((sum, rf, index) => {
      return sum + this.calcularRendimentoTotal(index);
    }, 0);
  }

  totalValorAtualRF(): number {
    return this.totalRendaFixa() + this.totalRendimentoRF();
  }

  totalValorFuturoRF(): number {
    return this.totalRendaFixa() + this.totalRendimentoTotalRF();
  }

  calcularRendimento(index: number): number {
    const rf = this.rendaFixaItems.at(index);
    if (!rf) return 0;

    const valor = rf.controls.valor_investido.value || 0;
    const prazo = rf.controls.prazo_meses.value || 0;
    const tipoTaxa = rf.controls.tipo_taxa.value;
    const dataAplicacao = rf.controls.data_aplicacao.value;

    let taxaAnual = 0;
    if (tipoTaxa === 'pos_fixado') {
      const pctCdi = rf.controls.percentual_cdi.value || 0;
      taxaAnual = (pctCdi / 100) * this.CDI_ATUAL;
    } else {
      taxaAnual = rf.controls.taxa.value || 0;
    }

    // Calcular tempo decorrido desde a aplicação
    let mesesDecorridos = 0;
    if (dataAplicacao) {
      const dataAplicacaoDate = new Date(dataAplicacao);
      const hoje = new Date();
      const diffMs = hoje.getTime() - dataAplicacaoDate.getTime();
      const diffDias = Math.max(0, diffMs / (1000 * 60 * 60 * 24));
      mesesDecorridos = Math.min(prazo, diffDias / 30.44);
    }

    // Conversão para taxa do período DECORRIDO (capitalização composta)
    const taxaPeriodoDecorrido = Math.pow(1 + taxaAnual / 100, mesesDecorridos / 12) - 1;
    const valorAtual = valor * (1 + taxaPeriodoDecorrido);
    const rendimentoBruto = valorAtual - valor;

    // Aplicar desconto de IR baseado no prazo TOTAL (tabela regressiva)
    const diasAproximados = prazo * 30.44;
    let aliquotaIR = 0.15; // Default para > 720 dias
    if (diasAproximados <= 180) {
      aliquotaIR = 0.225;
    } else if (diasAproximados <= 360) {
      aliquotaIR = 0.2;
    } else if (diasAproximados <= 720) {
      aliquotaIR = 0.175;
    }

    // LCI, LCA, CRI, CRA são isentos de IR
    const tipo = rf.controls.tipo.value;
    const isento = ['lci', 'lca', 'cri', 'cra'].includes(tipo);
    const ir = isento ? 0 : rendimentoBruto * aliquotaIR;

    return rendimentoBruto - ir;
  }

  calcularRendimentoTotal(index: number): number {
    const rf = this.rendaFixaItems.at(index);
    if (!rf) return 0;

    const valor = rf.controls.valor_investido.value || 0;
    const prazo = rf.controls.prazo_meses.value || 0;
    const tipoTaxa = rf.controls.tipo_taxa.value;

    let taxaAnual = 0;
    if (tipoTaxa === 'pos_fixado') {
      const pctCdi = rf.controls.percentual_cdi.value || 0;
      taxaAnual = (pctCdi / 100) * this.CDI_ATUAL;
    } else {
      taxaAnual = rf.controls.taxa.value || 0;
    }

    // Conversão para taxa do período TOTAL (capitalização composta)
    const taxaPeriodoTotal = Math.pow(1 + taxaAnual / 100, prazo / 12) - 1;
    const valorFinal = valor * (1 + taxaPeriodoTotal);
    const rendimentoBruto = valorFinal - valor;

    // Aplicar desconto de IR baseado no prazo TOTAL (tabela regressiva)
    const diasAproximados = prazo * 30.44;
    let aliquotaIR = 0.15; // Default para > 720 dias
    if (diasAproximados <= 180) {
      aliquotaIR = 0.225;
    } else if (diasAproximados <= 360) {
      aliquotaIR = 0.2;
    } else if (diasAproximados <= 720) {
      aliquotaIR = 0.175;
    }

    // LCI, LCA, CRI, CRA são isentos de IR
    const tipo = rf.controls.tipo.value;
    const isento = ['lci', 'lca', 'cri', 'cra'].includes(tipo);
    const ir = isento ? 0 : rendimentoBruto * aliquotaIR;

    return rendimentoBruto - ir;
  }

  calcularValorFinal(index: number): number {
    const rf = this.rendaFixaItems.at(index);
    if (!rf) return 0;
    const valorInvestido = rf.controls.valor_investido.value || 0;
    return valorInvestido + this.calcularRendimentoTotal(index);
  }

  avgTaxaRF(): number {
    if (this.rendaFixaItems.length === 0) return 0;
    const total = this.totalRendaFixa();
    if (total === 0) return 0;

    // Média ponderada pelo valor investido
    let somaPonderada = 0;
    this.rendaFixaItems.controls.forEach(rf => {
      const valor = rf.controls.valor_investido.value || 0;
      let taxa = 0;
      if (rf.controls.tipo_taxa.value === 'pos_fixado') {
        const pct_cdi = rf.controls.percentual_cdi.value || 0;
        taxa = (pct_cdi / 100) * this.CDI_ATUAL;
      } else {
        taxa = rf.controls.taxa.value || 0;
      }
      somaPonderada += taxa * valor;
    });
    return somaPonderada / total;
  }

  rfTipoLabel(tipo: RendaFixaTipo): string {
    const labels: Record<RendaFixaTipo, string> = {
      cdb: 'CDB',
      lci: 'LCI',
      lca: 'LCA',
      tesouro_selic: 'Tesouro Selic',
      tesouro_ipca: 'Tesouro IPCA+',
      tesouro_pre: 'Tesouro Pré',
      lc: 'LC',
      cri: 'CRI',
      cra: 'CRA',
    };
    return labels[tipo];
  }

  isIsentoIR(tipo: RendaFixaTipo): boolean {
    return ['lci', 'lca', 'cri', 'cra'].includes(tipo);
  }

  evaluateAssets(): void {
    const items = this.portfolioItems.getRawValue();
    const dy = this.form.controls.desired_yield.getRawValue();
    this.svc.evaluatePortfolio({ items, desired_yield: dy }).subscribe({
      next: res => {
        this.result.set(res);
      },
      error: () => {},
      complete: () => {},
    });
  }

  private loadStoredPortfolio(): void {
    this.svc.getPortfolio().subscribe({
      next: res => {
        res.items.forEach(item => {
          // Ignorar positions sintéticas de renda fixa (criadas em persistPortfolio)
          if (item.ticker.startsWith('RF_')) {
            return;
          }

          const group = this.fb.group<PortfolioItemForm>({
            ticker: this.fb.control(item.ticker, {
              nonNullable: true,
              validators: Validators.required,
            }),
            quantity: this.fb.control(item.quantity, {
              nonNullable: true,
              validators: [Validators.required, Validators.min(0.0001)],
            }),
            avg_price: this.fb.control(item.avg_price, {
              nonNullable: true,
              validators: [Validators.required, Validators.min(0.0001)],
            }),
            category: this.fb.control(item.category, { nonNullable: true }),
          });
          this.portfolioItems.push(group);
        });
      },
      error: () => {},
    });
  }

  private persistPortfolio(): void {
    const items = this.portfolioItems.getRawValue();

    // Converter renda fixa em positions sintéticas para incluir no cálculo do dashboard
    // Isso permite que o dashboard conte renda fixa na alocação por categoria
    const rfItems = this.rendaFixaItems.getRawValue();
    const rfPositions: PortfolioItem[] = rfItems.map((rf, index) => ({
      ticker: `RF_${rf.tipo}_${index + 1}`, // Ex: RF_cdb_1, RF_tesouro_2
      quantity: 1,
      avg_price: rf.valor_investido, // O preço médio é o valor investido
      category: 'renda_fixa', // Força categoria renda_fixa
    }));

    const allItems = [...items, ...rfPositions];
    if (allItems.length === 0) return;

    this.saveState.set('saving');
    this.svc.savePortfolio(allItems).subscribe({
      next: () => {
        this.saveState.set('saved');
        // Também persiste renda fixa no localStorage para edição
        this.persistRendaFixa();
        setTimeout(() => this.saveState.set('idle'), 2000);
      },
      error: () => {
        this.saveState.set('error');
        setTimeout(() => this.saveState.set('idle'), 3000);
      },
      complete: () => {},
    });
  }

  private loadStoredRendaFixa(): void {
    const stored = localStorage.getItem('portfolio_renda_fixa');
    if (!stored) return;

    try {
      const items = JSON.parse(stored);
      items.forEach((item: any) => {
        const group = this.fb.group<RendaFixaItemForm>({
          nome: this.fb.control(item.nome || '', {
            nonNullable: true,
            validators: Validators.required,
          }),
          tipo: this.fb.control(item.tipo || 'cdb', { nonNullable: true }),
          valor_investido: this.fb.control(item.valor_investido || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(1)],
          }),
          taxa: this.fb.control(item.taxa || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(0)],
          }),
          prazo_meses: this.fb.control(item.prazo_meses || 0, {
            nonNullable: true,
            validators: [Validators.required, Validators.min(1)],
          }),
          data_aplicacao: this.fb.control(item.data_aplicacao || '', {
            nonNullable: true,
            validators: Validators.required,
          }),
          tipo_taxa: this.fb.control(item.tipo_taxa || 'pre_fixado', { nonNullable: true }),
          percentual_cdi: this.fb.control(item.percentual_cdi || null),
        });
        this.rendaFixaItems.push(group);
      });
    } catch (e) {
      console.error('Erro ao carregar renda fixa:', e);
    }
  }

  private persistRendaFixa(): void {
    const items = this.rendaFixaItems.getRawValue();
    localStorage.setItem('portfolio_renda_fixa', JSON.stringify(items));
  }
}
