// web/src/app/modules/pos/pages/pos-cart/pos-cart.component.ts
//
// MODIFICADO (SaaS - A.5): POS sin conexión.
// - Sin internet, la venta en efectivo se guarda en una cola local
//   (IndexedDB) como "Registrada localmente" y se muestra un comprobante provisional.
// - Al volver la conexión las ventas por enviar se envían solas (también hay
//   un botón "Sincronizar ahora"); las rechazadas se muestran con su motivo.
// - La búsqueda de prendas y las sucursales usan una copia local cuando no
//   hay conexión, indicando la fecha de esa copia (puede estar desactualizada).
// - Sin conexión solo se aceptan ventas al contado en efectivo: tarjeta y QR
//   necesitan confirmación en línea.
// MODIFICADO: estados de la venta local según el enunciado (Registrada
// localmente, Enviada, Confirmada, Rechazada); las confirmadas quedan como
// historial con su número de venta. Sin conexión no se vende más de lo que
// indica el stock local guardado.
import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import * as QRCode from 'qrcode';
import { InventoryService } from '../../../inventory/services/inventory.service';
import { PosSaleService } from '../../services/pos-sale.service';
import {
  PosOfflineService,
  ResultadoSync,
  VentaLocal
} from '../../services/pos-offline.service';
interface ItemVenta {
  id_variante: number;
  nombre: string;
  precio: number;
  cantidad: number;
}
// El catálogo local se renueva solo si tiene más de 30 minutos.
const VIGENCIA_CATALOGO_MS = 30 * 60 * 1000;
@Component({
  selector: 'app-pos-cart',
  templateUrl: './pos-cart.component.html',
  styleUrls: ['./pos-cart.component.scss']
})
export class PosCartComponent implements OnInit, OnDestroy {
  // Búsqueda de productos
  terminoBusqueda = '';
  resultados: any[] = [];
  buscando = false;
  busquedaLocal = false;
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
  // NUEVO (A.5): modo sin conexión
  enLinea = true;
  ventasLocales: VentaLocal[] = [];
  sincronizando = false;
  resultadoSync: ResultadoSync | null = null;
  fechaCatalogo: string | null = null;
  totalCatalogo = 0;
  actualizandoCatalogo = false;
  private suscripciones = new Subscription();
  constructor(
    private inventoryService: InventoryService,
    private posSaleService: PosSaleService,
    private offline: PosOfflineService
  ) {}
  ngOnInit(): void {
    this.suscripciones.add(this.offline.enLinea$.subscribe(enLinea => {
      const recuperada = enLinea && !this.enLinea;
      this.enLinea = enLinea;
      if (!enLinea && this.metodoPago !== 'EFECTIVO') {
        this.metodoPago = 'EFECTIVO';
        this.qrDataUrl = null;
      }
      if (recuperada) {
        this.cargarSucursales();
      }
    }));
    this.suscripciones.add(this.offline.ventas$.subscribe(v => this.ventasLocales = v));
    this.suscripciones.add(this.offline.sincronizando$.subscribe(s => this.sincronizando = s));
    this.suscripciones.add(this.offline.resultado$.subscribe(r => this.resultadoSync = r));
    this.offline.recargar();
    this.cargarSucursales();
    this.prepararCatalogoLocal();
    // Si quedaron ventas pendientes de otra vez, se intentan enviar al entrar.
    this.offline.sincronizar();
  }
  ngOnDestroy(): void {
    this.suscripciones.unsubscribe();
  }
  get pendientes(): number {
    return this.ventasLocales.filter(v => v.estado === 'REGISTRADA' || v.estado === 'ENVIADA').length;
  }
  get confirmadas(): number {
    return this.ventasLocales.filter(v => v.estado === 'CONFIRMADA').length;
  }
  get rechazadas(): number {
    return this.ventasLocales.filter(v => v.estado === 'RECHAZADA').length;
  }
  cargarSucursales(): void {
    if (!this.enLinea) {
      this.cargarSucursalesLocales();
      return;
    }
    this.inventoryService.getSucursales().subscribe({
      next: (data: any) => {
        this.sucursales = data.results || data;
        this.offline.guardarSucursales(this.sucursales).catch(() => undefined);
      },
      error: (err) => {
        if (this.offline.esErrorDeRed(err)) {
          this.offline.marcarSinConexion();
        }
        this.cargarSucursalesLocales();
      }
    });
  }
  private async cargarSucursalesLocales(): Promise<void> {
    this.sucursales = await this.offline.sucursalesLocales();
  }
  // Usa la copia local; si no hay o es antigua y hay conexión, la renueva.
  private async prepararCatalogoLocal(): Promise<void> {
    const local = await this.offline.catalogoLocal();
    this.mostrarInfoCatalogo(local);
    const antiguo = !local || Date.now() - new Date(local.fecha).getTime() > VIGENCIA_CATALOGO_MS;
    if (this.enLinea && antiguo) {
      this.actualizarCatalogo();
    }
  }
  async actualizarCatalogo(): Promise<void> {
    if (!this.enLinea || this.actualizandoCatalogo) {
      return;
    }
    this.actualizandoCatalogo = true;
    try {
      this.mostrarInfoCatalogo(await this.offline.descargarCatalogo());
    } catch (err) {
      if (this.offline.esErrorDeRed(err)) {
        this.offline.marcarSinConexion();
      }
    } finally {
      this.actualizandoCatalogo = false;
    }
  }
  private mostrarInfoCatalogo(entrada: { fecha: string; datos: any[] } | null): void {
    this.fechaCatalogo = entrada?.fecha || null;
    this.totalCatalogo = entrada?.datos?.length || 0;
  }
  buscar(): void {
    if (!this.terminoBusqueda.trim()) {
      this.resultados = [];
      return;
    }
    if (!this.enLinea) {
      this.buscarEnCatalogoLocal();
      return;
    }
    this.buscando = true;
    this.busquedaLocal = false;
    this.inventoryService.getVariantes(this.terminoBusqueda).subscribe({
      next: (data: any) => {
        this.resultados = data.results || data;
        this.buscando = false;
      },
      error: (err) => {
        this.buscando = false;
        if (this.offline.esErrorDeRed(err)) {
          this.offline.marcarSinConexion();
          this.buscarEnCatalogoLocal();
        } else {
          this.resultados = [];
        }
      }
    });
  }
  private async buscarEnCatalogoLocal(): Promise<void> {
    this.busquedaLocal = true;
    this.resultados = await this.offline.buscarLocal(this.terminoBusqueda);
  }
  agregarItem(variante: any): void {
    const existente = this.items.find(i => i.id_variante === variante.id_variante);
    if (existente) {
      existente.cantidad += 1;
    } else {
      this.items.push({
        id_variante: variante.id_variante,
        nombre: variante.nombre_completo,
        precio: Number(variante.precio) || 0,
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
    this.error = null;
    if (!this.enLinea) {
      this.guardarSinConexion();
      return;
    }
    this.registrando = true;
    const itemsPayload = this.items.map(i => ({ id_variante: i.id_variante, cantidad: i.cantidad }));
    this.posSaleService.registrarVenta(this.sucursalSeleccionada, this.metodoPago, itemsPayload).subscribe({
      next: (venta) => {
        this.ventaConfirmada = venta;
        this.registrando = false;
      },
      error: (err) => {
        this.registrando = false;
        // Se cortó la conexión justo al registrar: la venta pasa a la cola local.
        if (this.offline.esErrorDeRed(err)) {
          this.offline.marcarSinConexion();
          this.guardarSinConexion();
          return;
        }
        this.error = err?.error?.error || err?.error?.detail || 'No se pudo registrar la venta. Intenta nuevamente.';
      }
    });
  }
  private async guardarSinConexion(): Promise<void> {
    if (this.metodoPago !== 'EFECTIVO') {
      this.error = 'Sin conexión solo se pueden registrar ventas al contado en efectivo.';
      return;
    }
    const sucursal = this.sucursales.find(s => s.id_sucursal === this.sucursalSeleccionada);
    this.registrando = true;
    try {
      const faltante = await this.offline.validarStockLocal(this.items);
      if (faltante) {
        this.error = faltante;
        return;
      }
      const venta = await this.offline.guardarVenta({
        id_sucursal: this.sucursalSeleccionada as number,
        sucursal: sucursal?.nombre || '',
        metodo_pago: this.metodoPago,
        items: this.items.map(i => ({ ...i }))
      });
      this.ventaConfirmada = { offline: true, ...venta };
    } catch {
      this.error = 'No se pudo guardar la venta en este dispositivo.';
    } finally {
      this.registrando = false;
    }
  }
  sincronizarAhora(): void {
    this.offline.sincronizar();
  }
  descartar(venta: VentaLocal): void {
    if (confirm('¿Descartar esta venta rechazada? Se borrará de este dispositivo.')) {
      this.offline.descartar(venta);
    }
  }
  limpiarConfirmadas(): void {
    this.offline.limpiarConfirmadas();
  }
  textoEstado(venta: VentaLocal): string {
    switch (venta.estado) {
      case 'CONFIRMADA':
        return venta.id_venta ? `Confirmada · Venta #${venta.id_venta}` : 'Confirmada';
      case 'RECHAZADA':
        return 'Rechazada';
      case 'ENVIADA':
        return 'Enviada';
      default:
        return 'Registrada localmente';
    }
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