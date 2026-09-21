// web/src/app/modules/assistant/components/chat-bubble/chat-bubble.component.ts
//
// NUEVO (CU18/CU19): globo de chat flotante del asistente virtual.
// Se coloca solo en el catálogo (no en el layout) y únicamente lo ve un
// usuario con sesión iniciada como CLIENTE.
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/auth/auth.service';
import { AssistantService, TarjetaPrenda } from '../../services/assistant.service';

interface ParteTexto {
  texto: string;
  negrita: boolean;
}

interface MensajeChat {
  autor: 'cliente' | 'asistente';
  partes: ParteTexto[];
  tarjetas: TarjetaPrenda[];
  error: boolean;
}

@Component({
  selector: 'app-chat-bubble',
  templateUrl: './chat-bubble.component.html',
  styleUrls: ['./chat-bubble.component.scss']
})
export class ChatBubbleComponent implements OnInit {
  @ViewChild('lista') lista?: ElementRef<HTMLDivElement>;

  visible = false;
  abierto = false;
  cargando = false;
  cargandoHistorial = false;
  private historialCargado = false;

  entrada = '';
  mensajes: MensajeChat[] = [];
  readonly maxCaracteres = 500;
  readonly sugerencias = [
    'Recomiéndame una polera',
    '¿Qué chaquetas tienen y cuánto cuestan?',
    '¿Qué sucursales tienen y en qué horario atienden?',
    '¿En qué estado está mi último pedido?'
  ];

  constructor(
    private authService: AuthService,
    private assistantService: AssistantService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.visible = this.authService.esCliente();
  }

  alternar(): void {
    this.abierto = !this.abierto;
    if (!this.abierto) {
      return;
    }
    if (this.historialCargado) {
      this.irAlFinal();
    } else {
      this.cargarHistorial();
    }
  }

  enviar(texto?: string): void {
    const mensaje = (texto ?? this.entrada).trim();
    if (!mensaje || this.cargando) {
      return;
    }
    this.mensajes.push(this.crearMensaje('cliente', mensaje));
    this.entrada = '';
    this.cargando = true;
    this.irAlFinal();

    this.assistantService.enviar(mensaje).subscribe({
      next: (respuesta) => {
        this.mensajes.push(
          this.crearMensaje('asistente', respuesta.respuesta, respuesta.tarjetas)
        );
        this.cargando = false;
        this.irAlFinal();
      },
      error: (err) => {
        const detalle = err?.error?.detail;
        this.mensajes.push(
          this.crearMensaje(
            'asistente',
            detalle || 'No pude responder en este momento. Intenta de nuevo en unos minutos.',
            [],
            true
          )
        );
        this.cargando = false;
        this.irAlFinal();
      }
    });
  }

  precio(t: TarjetaPrenda): string {
    const formato = (n: number) => `Bs ${Number(n).toFixed(2)}`;
    return t.precio_desde === t.precio_hasta
      ? formato(t.precio_desde)
      : `${formato(t.precio_desde)} - ${formato(t.precio_hasta)}`;
  }

  verDetalle(t: TarjetaPrenda): void {
    this.abierto = false;
    this.router.navigate(['/catalog', t.id_producto]);
  }

  private cargarHistorial(): void {
    this.cargandoHistorial = true;
    this.assistantService.historial().subscribe({
      next: (filas) => {
        const previos: MensajeChat[] = [];
        for (const fila of filas) {
          previos.push(this.crearMensaje('cliente', fila.mensaje));
          previos.push(this.crearMensaje('asistente', fila.respuesta));
        }
        this.mensajes = [...previos, ...this.mensajes];
        this.historialCargado = true;
        this.cargandoHistorial = false;
        this.irAlFinal();
      },
      error: () => {
        this.historialCargado = true;
        this.cargandoHistorial = false;
      }
    });
  }

  private crearMensaje(
    autor: 'cliente' | 'asistente',
    texto: string,
    tarjetas: TarjetaPrenda[] = [],
    error = false
  ): MensajeChat {
    return { autor, partes: this.aPartes(texto), tarjetas, error };
  }

  // El modelo responde con un Markdown mínimo: viñetas ("* ", "- ") y **negrita**.
  // Se convierte a partes de texto para mostrarlo sin usar innerHTML.
  private aPartes(texto: string): ParteTexto[] {
    const limpio = (texto || '').replace(/^[ \t]*[*-][ \t]+/gm, '• ');
    const partes: ParteTexto[] = [];
    const patron = /\*\*(.+?)\*\*/g;
    let ultimo = 0;
    let coincidencia: RegExpExecArray | null;
    while ((coincidencia = patron.exec(limpio)) !== null) {
      if (coincidencia.index > ultimo) {
        partes.push({ texto: limpio.slice(ultimo, coincidencia.index), negrita: false });
      }
      partes.push({ texto: coincidencia[1], negrita: true });
      ultimo = coincidencia.index + coincidencia[0].length;
    }
    if (ultimo < limpio.length) {
      partes.push({ texto: limpio.slice(ultimo), negrita: false });
    }
    return partes;
  }

  private irAlFinal(): void {
    setTimeout(() => {
      const el = this.lista?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    }, 0);
  }
}