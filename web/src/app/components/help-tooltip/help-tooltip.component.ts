import { Component, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-help-tooltip',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    <span class="relative group inline-flex items-center cursor-help ml-1">
      <lucide-icon name="circle-question-mark" size="12" class="text-ink-2"></lucide-icon>
      <span
        class="fi-caption pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-56 -translate-x-1/2 rounded-lg bg-ground-1 border border-hairline px-3 py-2 text-ink shadow-popover opacity-0 group-hover:opacity-100 transition-opacity duration-150 leading-relaxed"
      >
        {{ text() }}
      </span>
    </span>
  `,
})
export class HelpTooltipComponent {
  text = input.required<string>();
}
