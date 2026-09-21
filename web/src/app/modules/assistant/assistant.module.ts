// web/src/app/modules/assistant/assistant.module.ts
//
// NUEVO (CU18/CU19): módulo del asistente virtual. Lo importa solo CatalogModule,
// así el globo de chat existe únicamente en el catálogo y no en el layout.
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatBubbleComponent } from './components/chat-bubble/chat-bubble.component';

@NgModule({
  declarations: [ChatBubbleComponent],
  imports: [CommonModule, FormsModule],
  exports: [ChatBubbleComponent]
})
export class AssistantModule {}