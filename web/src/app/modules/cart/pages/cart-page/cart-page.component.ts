import { Component, OnInit } from '@angular/core';
import { CartService } from '../../services/cart.service';

@Component({
  selector: 'app-cart-page',
  templateUrl: './cart-page.component.html',
  styleUrls: ['./cart-page.component.scss']
})
export class CartPageComponent implements OnInit {
  carrito: any = null;
  loading = false;

  constructor(private cartService: CartService) {}

  ngOnInit(): void {
    this.cargarCarrito();
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
}