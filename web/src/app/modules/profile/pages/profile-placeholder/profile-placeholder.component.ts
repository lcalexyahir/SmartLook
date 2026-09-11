// web/src/app/modules/profile/pages/profile-placeholder/profile-placeholder.component.ts
//
// Archivo NUEVO. Placeholder, mismo criterio que la pestaña "Perfil"
// del bottom nav en mobile.

import { Component } from '@angular/core';

@Component({
  selector: 'app-profile-placeholder',
  template: `
    <div class="placeholder-container">
      <h2>Perfil</h2>
      <p>Próximamente podrás editar tus datos y ver tu historial aquí.</p>
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
export class ProfilePlaceholderComponent { }