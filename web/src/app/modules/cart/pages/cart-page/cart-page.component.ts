import { Component, OnInit, AfterViewChecked } from '@angular/core';
import { loadStripe, Stripe, StripeCardElement, StripeElements } from '@stripe/stripe-js';
import { environment } from '../../../../../environments/environment';
import { CartService, DatosEntrega } from '../../services/cart.service';
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

  // CU21: retiro en sucursal o delivery a domicilio
  tipoEntrega: 'RETIRO' | 'DELIVERY' = 'RETIRO';
  direccion = '';
  referencia = '';
  latitud: number | null = null;
  longitud: number | null = null;
  ubicando = false;
  cotizando = false;
  cotizacion: any = null;
  sucursalMapa: { nombre: string; latitud: number | null; longitud: number | null } | null = null;
  private geocodificacionId = 0;

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

  // Total a cobrar: prendas + envío (solo si es delivery y ya hay cotización).
  get totalAPagar(): number {
    const productos = Number(this.carrito?.total) || 0;
    const envio = this.tipoEntrega === 'DELIVERY' && this.cotizacion
      ? Number(this.cotizacion.costo_envio) || 0
      : 0;
    return productos + envio;
  }

  cargarCarrito(): void {
    this.loading = true;
    this.cartService.getCarritoActual().subscribe({
      next: (data) => {
        this.carrito = data;
        this.loading = false;
        // Si cambió la cantidad de prendas, el costo de envío también puede cambiar.
        if (
          this.tipoEntrega === 'DELIVERY' &&
          this.latitud !== null &&
          !this.ordenConfirmada &&
          data?.items?.length > 0
        ) {
          this.cotizar();
        }
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

  // ---- CU21: entrega ----

  onCambioTipoEntrega(): void {
    this.cotizacion = null;
    this.errorPago = null;
    // Al volver a Delivery con una ubicación ya elegida, se recotiza sola.
    if (this.tipoEntrega === 'DELIVERY' && this.latitud !== null && this.sucursalSeleccionada) {
      this.cotizar();
    }
  }

  onCambioSucursal(): void {
    this.cotizacion = null;
    this.errorPago = null;
    // Sucursal elegida, con sus coordenadas, para dibujarla en el mapa.
    const s = this.sucursales.find(x => x.id_sucursal === this.sucursalSeleccionada);
    this.sucursalMapa = s && s.latitud != null && s.longitud != null
      ? { nombre: s.nombre, latitud: Number(s.latitud), longitud: Number(s.longitud) }
      : null;
    if (this.tipoEntrega === 'DELIVERY' && this.latitud !== null) {
      this.cotizar();
    }
  }

  usarMiUbicacion(): void {
    if (!navigator.geolocation) {
      this.errorPago = 'Tu navegador no permite obtener la ubicación.';
      return;
    }
    this.ubicando = true;
    this.errorPago = null;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.latitud = pos.coords.latitude;
        this.longitud = pos.coords.longitude;
        this.ubicando = false;
        this.completarDireccion(this.latitud, this.longitud);
        this.cotizar();
      },
      () => {
        this.ubicando = false;
        this.errorPago = 'No se pudo obtener tu ubicación. Permite el acceso a la ubicación e intenta de nuevo.';
      },
      { enableHighAccuracy: true, timeout: 15000 }
    );
  }

  // El cliente tocó el mapa o arrastró el punto: se guarda, se completa la dirección y se recotiza el envío.
  onUbicacionMapa(punto: { lat: number; lng: number }): void {
    this.latitud = punto.lat;
    this.longitud = punto.lng;
    this.completarDireccion(punto.lat, punto.lng);
    this.cotizar();
  }

  // Rellena "Dirección de entrega" con la dirección del punto elegido (OpenStreetMap / Nominatim).
  // Se usa fetch y no HttpClient para que el token de sesión no se envíe a un servicio externo.
  private async completarDireccion(lat: number, lng: number): Promise<void> {
    const id = ++this.geocodificacionId;
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&accept-language=es`;
      const resp = await fetch(url);
      if (!resp.ok) {
        return;
      }
      const data = await resp.json();
      // Si el cliente movió el punto otra vez mientras esperaba, se descarta esta respuesta.
      if (id === this.geocodificacionId && data?.display_name) {
        this.direccion = String(data.display_name).slice(0, 250);
      }
    } catch {
      // Si falla, el cliente puede escribir la dirección a mano.
    }
  }

  cotizar(): void {
    if (!this.sucursalSeleccionada) {
      this.errorPago = 'Selecciona primero la sucursal que despacha tu pedido.';
      return;
    }
    if (this.latitud === null || this.longitud === null) {
      return;
    }
    this.cotizando = true;
    this.errorPago = null;
    this.cartService.cotizarEnvio(this.sucursalSeleccionada, this.latitud, this.longitud).subscribe({
      next: (data) => {
        this.cotizacion = data;
        this.cotizando = false;
      },
      error: (err) => {
        this.cotizacion = null;
        this.cotizando = false;
        this.errorPago = err?.error?.error || 'No se pudo cotizar el envío.';
      }
    });
  }

  // Paso 1: valida el carrito/stock en el backend y crea el intento de pago en Stripe.
  iniciarPago(): void {
    if (!this.sucursalSeleccionada) {
      this.errorPago = this.tipoEntrega === 'DELIVERY'
        ? 'Selecciona la sucursal que despacha tu pedido.'
        : 'Selecciona una sucursal de entrega/retiro.';
      return;
    }

    let entrega: DatosEntrega | undefined;
    if (this.tipoEntrega === 'DELIVERY') {
      if (!this.direccion.trim()) {
        this.errorPago = 'Ingresa tu dirección de entrega.';
        return;
      }
      if (this.latitud === null || this.longitud === null) {
        this.errorPago = 'Marca tu ubicación en el mapa o toca "Usar mi ubicación" para calcular el envío.';
        return;
      }
      if (!this.cotizacion) {
        this.errorPago = 'Espera a que se calcule el costo de envío.';
        return;
      }
      entrega = {
        direccion: this.direccion.trim(),
        referencia: this.referencia.trim(),
        latitud: this.latitud,
        longitud: this.longitud
      };
    }

    this.iniciandoPago = true;
    this.errorPago = null;
    this.cartService.checkout(this.sucursalSeleccionada, entrega).subscribe({
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