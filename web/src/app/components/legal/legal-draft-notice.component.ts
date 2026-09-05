import { Component } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-legal-draft-notice',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    <div class="notice notice-attention mb-8">
      <lucide-icon name="triangle-alert" size="18" aria-hidden="true"></lucide-icon>
      <div>
        <p class="fi-label m-0">Minuta — ainda não revisada por advogado</p>
        <p class="fi-body m-0 mt-1">
          Este texto descreve com honestidade como o fiance funciona hoje, mas ainda não passou por
          revisão jurídica. Enquanto este aviso estiver aqui, ele vale como declaração de
          transparência, não como instrumento contratual definitivo.
        </p>
      </div>
    </div>
  `,
})
export class LegalDraftNoticeComponent {}
