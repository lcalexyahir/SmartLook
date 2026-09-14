import { Component, OnInit } from '@angular/core';
import { CartService } from '../../services/cart.service';
import { InventoryService } from '../../../inventory/services/inventory.service';

@Component({
  selector: 'app-cart-page',
  templateUrl: './cart-page.component.html',
  styleUrls: ['./cart-page.component.scss']
})
export class CartPageComponent implements OnInit {
  carrito: any = null;
  loading = false;
  sucursales: any[] = [];
  sucursalSeleccionada: number | null = null;
  procesandoPago = false;
  errorPago: string | null = null;
  ordenConfirmada: any = null;

  constructor(
    private cartService: CartService,
    private inventoryService: InventoryService
  ) {}

  ngOnInit(): void {
    this.cargarCarrito();
    this.cargarSucursales();
  }

  cargarCarrito(): void {
    this.loading = true;
    this.cartService.getCarritoActual().subscribe({
      next: (data) => {
        this.carrito = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  cargarSucursales(): void {
    this.inventoryService.getSucursales().subscribe({
      next: (data: any) => this.sucursales = data.results || data,
      error: () => this.sucursales = []
    });
  }

  incrementar(item: any): void {
    this.cartService.actualizarCantidad(item.id_item, item.cantidad + 1).subscribe({
      next: () => this.cargarCarrito()
    });
  }

  decrementar(item: any): void {
    if (item.cantidad <= 1) {
      this.quitar(item);
      return;
    }
    this.cartService.actualizarCantidad(item.id_item, item.cantidad - 1).subscribe({
      next: () => this.cargarCarrito()
    });
  }

  quitar(item: any): void {
    this.cartService.quitarItem(item.id_item).subscribe({
      next: () => this.cargarCarrito()
    });
  }

  procesarPago(): void {
    if (!this.sucursalSeleccionada) {
      this.errorPago = 'Selecciona una sucursal de entrega/retiro.';
      return;
    }
    this.procesandoPago = true;
    this.errorPago = null;
    this.ordenConfirmada = null;

    this.cartService.checkout(this.sucursalSeleccionada).subscribe({
      next: (orden) => {
        this.ordenConfirmada = orden;
        this.procesandoPago = false;
        this.cargarCarrito();
      },
      error: (err) => {
        this.errorPago = err?.error?.error || 'No se pudo procesar el pago. Intenta nuevamente.';
        this.procesandoPago = false;
      }
    });
  }
}