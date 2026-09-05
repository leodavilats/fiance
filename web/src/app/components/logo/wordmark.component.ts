import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';

interface Letra {
  readonly d: string;
  readonly x: number;
}

const AVANCOS: readonly [number, string][] = [
  [62, 'M0 0L62 0L62 13L13 13L13 49L50 49L50 62L13 62L13 100L0 100Z'],
  [13, 'M0 0L13 0L13 100L0 100Z'],
  [74, 'M29 0L45 0L74 100L59.5 100L37 22.4L14.5 100L0 100Z M29.29 49L44.71 49L48.48 62L25.52 62Z'],
  [72, 'M0 0L13 0L59 76L59 0L72 0L72 100L59 100L13 24L13 100L0 100Z'],
  [70, 'M64.4 22.8A35 50 0 1 0 64.4 77.2L53.4 70.2A22 37 0 1 1 53.4 29.8Z'],
  [62, 'M0 0L62 0L62 13L13 13L13 49L48 49L48 62L13 62L13 87L62 87L62 100L0 100Z'],
];
const ENTRELETRA = 13;

function layout(): { letras: Letra[]; largura: number } {
  let x = 0;
  const letras: Letra[] = [];
  for (const [avanco, d] of AVANCOS) {
    letras.push({ d, x });
    x += avanco + ENTRELETRA;
  }
  return { letras, largura: x - ENTRELETRA };
}

const { letras: LETRAS, largura: LARGURA } = layout();

@Component({
  selector: 'app-wordmark',
  standalone: true,
  imports: [CommonModule],
  template: `
    <svg
      [attr.viewBox]="'0 0 ' + largura + ' 100'"
      [attr.width]="(height() * largura) / 100"
      [attr.height]="height()"
      [attr.role]="decorative() ? null : 'img'"
      [attr.aria-label]="decorative() ? null : 'fiance'"
      [attr.aria-hidden]="decorative() ? 'true' : null"
      focusable="false"
    >
      <g [style.fill]="color()">
        <path [attr.d]="letras[0].d" [attr.transform]="'translate(' + letras[0].x + ' 0)'" />
        <path [attr.d]="letras[1].d" [attr.transform]="'translate(' + letras[1].x + ' 0)'" />
        <path [attr.d]="letras[2].d" [attr.transform]="'translate(' + letras[2].x + ' 0)'" />
        <path [attr.d]="letras[3].d" [attr.transform]="'translate(' + letras[3].x + ' 0)'" />
        <path [attr.d]="letras[4].d" [attr.transform]="'translate(' + letras[4].x + ' 0)'" />
        <path [attr.d]="letras[5].d" [attr.transform]="'translate(' + letras[5].x + ' 0)'" />
      </g>
    </svg>
  `,
})
export class WordmarkComponent {
  readonly height = input<number>(18);
  readonly color = input<string>('var(--fi-ink-1)');
  readonly decorative = input<boolean>(false);
  protected readonly letras = LETRAS;
  protected readonly largura = LARGURA;
}
