import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { SnackbarService } from '../../core';

@Component({
  selector: 'app-snackbar',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './snackbar.component.html',
  styleUrls: ['./snackbar.component.scss'],
})
export class SnackbarComponent {
  readonly snackbar = inject(SnackbarService);
}
