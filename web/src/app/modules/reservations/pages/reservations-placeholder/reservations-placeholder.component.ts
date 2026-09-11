// web/src/app/modules/reservations/pages/reservations-placeholder/reservations-placeholder.component.ts
//
// Archivo NUEVO. Placeholder, mismo criterio que la pestaña "Reservas"
// del bottom nav en mobile - listo para cuando se construya el caso de
// uso real de reservas.

import { Component } from '@angular/core';

@Component({
  selector: 'app-reservations-placeholder',
  template: `
    <div class="placeholder-container">
      <h2>Reservas</h2>
      <p>Próximamente podrás reservar prendas para probarlas en tienda.</p>
    </div>
  `,
  styles: [`
    .placeholder-container {
      padding: 3rem;
      text-align: center;
      color: #6B6459;
    }
    h2 {
      color: #1E1A16;
      margin-bottom: 0.5rem;
    }
  `]
})
export class ReservationsPlaceholderComponent { }