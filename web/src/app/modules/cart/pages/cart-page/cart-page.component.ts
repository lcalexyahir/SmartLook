import { Component, OnInit, AfterViewChecked } from '@angular/core';
import { loadStripe, Stripe, StripeCardElement, StripeElements } from '@stripe/stripe-js';
import { environment } from '../../../../../environments/environment';
import { CartService } from '../../services/cart.service';
import { InventoryService } from '../../../inventory/services/inventory.service';

@Component({
  selector: 'app-cart-page',
  templateUrl: './cart-page.component.html',
  styleUrls: ['./cart-page.component.scss']
})
export class CartPageComponent implements OnInit, AfterViewChecked {
  carrito: any = null;
  loading = false;
  sucursales: any[] = [];
  sucursalSeleccionada: number | null = null;
  errorPago: string | null = null;
  ordenConfirmada: any = null;

  // Flujo de pago con Stripe
  mostrarFormularioPago = false;
  iniciandoPago = false;
  confirmandoPago = false;
  private stripe: Stripe | null = null;
  private elements: StripeElements | null = null;
  private cardElement: StripeCardElement | null = null;
  private cardElementMontado = false;
  private clientSecret: string | null = null;
  private ordenPendiente: any = null;

  constructor(
    private cartService: CartService,
    private inventoryService: InventoryService
  ) {}

  ngOnInit(): void {
    this.cargarCarrito();
    this.cargarSucursales();
    loadStripe(environment.stripePublishableKey).then((stripe) => {
      this.stripe = stripe;
    });
  }

  ngAfterViewChecked(): void {
    // Monta el campo de tarjeta apenas el div del formulario existe en el DOM
    // (aparece recién cuando mostrarFormularioPago pasa a true).
    if (this.mostrarFormularioPago && this.stripe && !this.cardElementMontado) {
      const contenedor = document.getElementById('card-element');
      if (contenedor) {
        this.elements = this.stripe.elements();
        this.cardElement = this.elements.create('card');
        this.cardElement.mount('#card-element');
        this.cardElementMontado = true;
      }
    }
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

  // Paso 1: valida el carrito/stock en el backend y crea el intento de pago en Stripe.
  iniciarPago(): void {
    if (!this.sucursalSeleccionada) {
      this.errorPago = 'Selecciona una sucursal de entrega/retiro.';
      return;
    }
    this.iniciandoPago = true;
    this.errorPago = null;

    this.cartService.checkout(this.sucursalSeleccionada).subscribe({
      next: (data) => {
        this.clientSecret = data.client_secret;
        this.ordenPendiente = data.orden;
        this.mostrarFormularioPago = true;
        this.iniciandoPago = false;
      },
      error: (err) => {
        this.errorPago = err?.error?.error || 'No se pudo iniciar el pago. Intenta nuevamente.';
        this.iniciandoPago = false;
      }
    });
  }

  // Paso 2: confirma la tarjeta ingresada con Stripe y cierra la orden en el backend.
  async confirmarPago(): Promise<void> {
    if (!this.stripe || !this.cardElement || !this.clientSecret) {
      return;
    }
    this.confirmandoPago = true;
    this.errorPago = null;

    const resultado = await this.stripe.confirmCardPayment(this.clientSecret, {
      payment_method: { card: this.cardElement }
    });

    if (resultado.error) {
      this.errorPago = resultado.error.message || 'La tarjeta fue rechazada.';
      this.confirmandoPago = false;
      return;
    }

    const paymentIntentId = resultado.paymentIntent?.id;
    if (!paymentIntentId) {
      this.errorPago = 'No se pudo confirmar el pago.';
      this.confirmandoPago = false;
      return;
    }

    this.cartService.confirmarPago(paymentIntentId).subscribe({
      next: (orden) => {
        this.ordenConfirmada = orden;
        this.confirmandoPago = false;
        this.mostrarFormularioPago = false;
        this.cargarCarrito();
      },
      error: (err) => {
        this.errorPago = err?.error?.error || 'No se pudo cerrar la orden.';
        this.confirmandoPago = false;
      }
    });
  }

  cancelarPago(): void {
    this.mostrarFormularioPago = false;
    this.cardElementMontado = false;
    this.clientSecret = null;
    this.errorPago = null;
  }
}