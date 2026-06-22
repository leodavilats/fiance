import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal, computed, effect, Renderer2 } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import {
  AssetType,
  DipAnalysisResponse,
  LoadingService,
  Opportunity,
  RecommendService,
  UiHelperService,
} from '../../core';

type SortKey = 'score' | 'dy' | 'mos' | 'price';

@Component({
  selector: 'app-opportunities',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './opportunities.component.html',
})
export class OpportunitiesComponent implements OnInit {
  private svc = inject(RecommendService);
  private renderer = inject(Renderer2);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);
  readonly Math = Math;

  readonly CATEGORY_FILTERS = [
    { key: 'all', label: 'Todas' },
    { key: 'fiis', label: 'FIIs' },
    { key: 'acoes_br', label: 'Ações BR' },
    { key: 'acoes_int', label: 'Ações INT' },
    { key: 'cripto', label: 'Cripto' },
  ];

  constructor() {
    effect(() => {
      if (this.showDipPanel()) {
        this.renderer.addClass(document.body, 'overflow-hidden');
      } else {
        this.renderer.removeClass(document.body, 'overflow-hidden');
      }
    });
  }

  opps = signal<Opportunity[] | null>(null);
  cashAvailable = signal(0);
  totalItems = signal(0);
  totalPages = signal(0);
  currentPage = signal(1);
  pageSize = signal(50);

  filterText = signal('');
  filterMinDy = signal<number | null>(null);
  filterMinMos = signal<number | null>(null);
  filterSector = signal('');
  filterType = signal<'all' | AssetType>('all');
  filterCategory = signal<string>('all');
  sortKey = signal<SortKey>('score');
  sortOrder = signal<'asc' | 'desc'>('desc');
  includeHeld = signal(true);
  onlyInteresting = signal(false);

  showDipPanel = signal(false);
  dipPanelResult = signal<DipAnalysisResponse | null>(null);

  availableSectors = computed(() => {
    const list = this.opps() || [];
    return [...new Set(list.map(o => o.sector).filter(s => s))];
  });

  ngOnInit(): void {}

  search(): void {
    this.currentPage.set(1);
    this.loadOpportunities();
  }

  loadOpportunities(): void {
    const assetType = this.filterType() === 'all' ? '' : this.filterType();
    const category = this.filterCategory() === 'all' ? '' : this.filterCategory();

    this.svc
      .opportunities(
        this.includeHeld(),
        this.currentPage(),
        this.pageSize(),
        this.sortKey(),
        this.sortOrder(),
        this.filterText(),
        this.filterMinDy(),
        this.filterMinMos(),
        this.filterSector(),
        assetType,
        category,
        this.onlyInteresting()
      )
      .subscribe({
        next: res => {
          this.opps.set(res.items);
          this.cashAvailable.set(res.cash_available);
          this.totalItems.set(res.total_items);
          this.totalPages.set(res.total_pages);
          this.currentPage.set(res.current_page);
          this.pageSize.set(res.page_size);
        },
        error: () => {},
        complete: () => {},
      });
  }

  nextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.set(this.currentPage() + 1);
      this.loadOpportunities();
    }
  }

  prevPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.set(this.currentPage() - 1);
      this.loadOpportunities();
    }
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages()) {
      this.currentPage.set(page);
      this.loadOpportunities();
    }
  }

  changeSortKey(key: SortKey): void {
    if (this.sortKey() === key) {
      this.sortOrder.set(this.sortOrder() === 'desc' ? 'asc' : 'desc');
    } else {
      this.sortKey.set(key);
      this.sortOrder.set('desc');
    }
  }

  updateCash(ev: Event): void {
    const value = parseFloat((ev.target as HTMLInputElement).value);
    this.svc.savePreferences(value).subscribe({
      next: () => {
        this.cashAvailable.set(value);
      },
      error: () => {},
      complete: () => {},
    });
  }

  openDipAnalysis(symbol: string): void {
    this.showDipPanel.set(true);
    this.dipPanelResult.set(null);
    this.svc.dipAnalysis(symbol).subscribe({
      next: res => {
        this.dipPanelResult.set(res);
      },
      error: () => {
        this.closeDipPanel();
      },
    });
  }

  closeDipPanel(): void {
    this.showDipPanel.set(false);
    this.dipPanelResult.set(null);
  }
}
