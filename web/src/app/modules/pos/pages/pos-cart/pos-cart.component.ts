import { Component, OnInit } from '@angular/core';
import * as QRCode from 'qrcode';
import { InventoryService } from '../../../inventory/services/inventory.service';
import { PosSaleService } from '../../services/pos-sale.service';

interface ItemVenta {
  id_variante: number;
  nombre: string;
  precio: number;
  cantidad: number;
}

@Component({
  selector: 'app-pos-cart',
  templateUrl: './pos-cart.component.html',
  styleUrls: ['./pos-cart.component.scss']
})
export class PosCartComponent implements OnInit {
  // Búsqueda de productos
  terminoBusqueda = '';
  resultados: any[] = [];
  buscando = false;

  // Venta en curso (no persiste en el backend hasta "Registrar Venta")
  items: ItemVenta[] = [];
  sucursales: any[] = [];
  sucursalSeleccionada: number | null = null;
  metodoPago: string = 'EFECTIVO';

  // QR de cobro (visual, sin conexión bancaria real - ver nota en el informe)
  qrDataUrl: string | null = null;

  // Estado de registro
  registrando = false;
  error: string | null = null;
  ventaConfirmada: any = null;

  constructor(
    private inventoryService: InventoryService,
    private posSaleService: PosSaleService
  ) {}

  ngOnInit(): void {
    this.cargarSucursales();
  }

  cargarSucursales(): void {
    this.inventoryService.getSucursales().subscribe({
      next: (data: any) => this.sucursales = data.results || data,
      error: () => this.sucursales = []
    });
  }

  buscar(): void {
    if (!this.terminoBusqueda.trim()) {
      this.resultados = [];
      return;
    }
    this.buscando = true;
    this.inventoryService.getVariantes(this.terminoBusqueda).subscribe({
      next: (data: any) => {
        this.resultados = data.results || data;
        this.buscando = false;
      },
      error: () => {
        this.resultados = [];
        this.buscando = false;
      }
    });
  }

  agregarItem(variante: any): void {
    const existente = this.items.find(i => i.id_variante === variante.id_variante);
    if (existente) {
      existente.cantidad += 1;
    } else {
      this.items.push({
        id_variante: variante.id_variante,
        nombre: variante.nombre_completo,
        precio: variante.precio,
        cantidad: 1,
      });
    }
    this.actualizarQrSiCorresponde();
  }

  incrementar(item: ItemVenta): void {
    item.cantidad += 1;
    this.actualizarQrSiCorresponde();
  }

  decrementar(item: ItemVenta): void {
    if (item.cantidad <= 1) {
      this.quitar(item);
      return;
    }
    item.cantidad -= 1;
    this.actualizarQrSiCorresponde();
  }

  quitar(item: ItemVenta): void {
    this.items = this.items.filter(i => i !== item);
    this.actualizarQrSiCorresponde();
  }

  get total(): number {
    return this.items.reduce((acc, item) => acc + item.precio * item.cantidad, 0);
  }

  onMetodoPagoChange(): void {
    if (this.metodoPago === 'QR') {
      this.generarQr();
    } else {
      this.qrDataUrl = null;
    }
  }

  private actualizarQrSiCorresponde(): void {
    if (this.metodoPago === 'QR') {
      this.generarQr();
    }
  }

  async generarQr(): Promise<void> {
    const referencia = `SL-${Date.now()}`;
    const contenido = `SmartLook - Pago QR\nTotal: Bs ${this.total.toFixed(2)}\nReferencia: ${referencia}`;
    try {
      this.qrDataUrl = await QRCode.toDataURL(contenido, { width: 220 });
    } catch {
      this.qrDataUrl = null;
    }
  }

  registrarVenta(): void {
    if (this.items.length === 0) {
      this.error = 'Agrega al menos una prenda a la venta.';
      return;
    }
    if (!this.sucursalSeleccionada) {
      this.error = 'Selecciona la sucursal.';
      return;
    }

    this.registrando = true;
    this.error = null;

    const itemsPayload = this.items.map(i => ({ id_variante: i.id_variante, cantidad: i.cantidad }));

    this.posSaleService.registrarVenta(this.sucursalSeleccionada, this.metodoPago, itemsPayload).subscribe({
      next: (venta) => {
        this.ventaConfirmada = venta;
        this.registrando = false;
      },
      error: (err) => {
        this.error = err?.error?.error || 'No se pudo registrar la venta. Intenta nuevamente.';
        this.registrando = false;
      }
    });
  }

  nuevaVenta(): void {
    this.items = [];
    this.terminoBusqueda = '';
    this.resultados = [];
    this.sucursalSeleccionada = null;
    this.metodoPago = 'EFECTIVO';
    this.qrDataUrl = null;
    this.ventaConfirmada = null;
    this.error = null;
  }
}