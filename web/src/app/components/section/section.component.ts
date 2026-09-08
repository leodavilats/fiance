import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-section',
  standalone: true,
  // `fi-block` vai no host: um wrapper faria `.fi-block:first-child` olhar o wrapper.
  host: { class: 'fi-block' },
  template: `
    <div class="flex items-baseline justify-between gap-4 flex-wrap">
      <h2 [class]="headingClass()">{{ heading() }}</h2>
      <ng-content select="[sectionActions]" />
    </div>

    @if (hint()) {
      <p class="fi-body text-ink-2 m-0 mt-1 max-w-reading">{{ hint() }}</p>
    }

    <ng-content />
  `,
})
export class SectionComponent {
  readonly title = input.required<string>();

  /** Texto de apoio sob o título, quando a seção precisa dizer o que ela é. */
  readonly hint = input<string>('');

  /** Sufixo `· N`, para seção cujo título carrega quantidade ("A vencer · 3"). */
  readonly count = input<number | null>(null);

  /** `eyebrow` mantém a aparência de rótulo; `title` fica para a seção que é mesmo um título. */
  readonly tone = input<'eyebrow' | 'title'>('eyebrow');

  protected readonly heading = computed(() => {
    const n = this.count();
    return n === null ? this.title() : `${this.title()} · ${n}`;
  });

  protected readonly headingClass = computed(() =>
    this.tone() === 'title' ? 'fi-title text-ink m-0' : 'fi-eyebrow text-ink-3 m-0'
  );
}
