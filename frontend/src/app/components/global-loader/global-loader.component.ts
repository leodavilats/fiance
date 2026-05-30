import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { LoadingService } from '../../core';

@Component({
  selector: 'app-global-loader',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './global-loader.component.html',
  styleUrls: ['./global-loader.component.scss'],
})
export class GlobalLoaderComponent {
  readonly loading = inject(LoadingService);
}
