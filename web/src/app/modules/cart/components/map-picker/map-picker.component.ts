import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  NgZone,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild
} from '@angular/core';
import * as L from 'leaflet';

export interface PuntoMapa {
  lat: number;
  lng: number;
}

// CU21: mapa (Leaflet + OpenStreetMap, sin clave de API) para elegir el punto de entrega.
@Component({
  selector: 'app-map-picker',
  template: `
    <div class="map-wrapper">
      <div #mapa class="map"></div>
      <p class="map-hint">Toca el mapa o arrastra el punto azul para indicar dónde entregamos tu pedido.</p>
    </div>
  `,
  styles: [`
    .map {
      height: 300px;
      width: 100%;
      border-radius: 8px;
      border: 1px solid #e0e0e0;
      z-index: 0;
    }
    .map-hint {
      font-size: 0.8rem;
      color: #777;
      margin: 0.4rem 0 0;
    }
  `]
})
export class MapPickerComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() sucursal: { nombre: string; latitud: number | null; longitud: number | null } | null = null;
  @Input() latitud: number | null = null;
  @Input() longitud: number | null = null;
  @Output() ubicacionChange = new EventEmitter<PuntoMapa>();

  @ViewChild('mapa', { static: true }) mapaRef!: ElementRef<HTMLDivElement>;

  private map: L.Map | null = null;
  private clienteMarker: L.Marker | null = null;
  private sucursalMarker: L.Marker | null = null;
  private readonly centroDefecto: L.LatLngExpression = [-17.7834, -63.1821]; // Santa Cruz de la Sierra

  constructor(private zone: NgZone) {}

  ngAfterViewInit(): void {
    // Leaflet corre fuera de la zona de Angular para no disparar detección de cambios en cada movimiento.
    this.zone.runOutsideAngular(() => {
      this.map = L.map(this.mapaRef.nativeElement, { center: this.centroDefecto, zoom: 13 });
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      }).addTo(this.map);
      this.map.on('click', (e: L.LeafletMouseEvent) => {
        this.colocarCliente(e.latlng.lat, e.latlng.lng, true);
      });
    });
    this.actualizarMarcadores();
    // El mapa se crea dentro de un bloque que aparece dinámicamente: recalcula su tamaño.
    setTimeout(() => this.map?.invalidateSize(), 0);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.map) {
      this.actualizarMarcadores();
    }
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }

  private actualizarMarcadores(): void {
    if (!this.map) {
      return;
    }

    // Marcador de la sucursal
    if (this.sucursal && this.sucursal.latitud !== null && this.sucursal.longitud !== null) {
      const pos: L.LatLngExpression = [Number(this.sucursal.latitud), Number(this.sucursal.longitud)];
      if (!this.sucursalMarker) {
        this.sucursalMarker = L.marker(pos, { icon: this.icono('#e94560') }).addTo(this.map);
      } else {
        this.sucursalMarker.setLatLng(pos);
      }
      this.sucursalMarker.bindTooltip(`Sucursal: ${this.sucursal.nombre}`);
      if (this.latitud === null) {
        this.map.setView(pos, 14);
      }
    } else if (this.sucursalMarker) {
      this.sucursalMarker.remove();
      this.sucursalMarker = null;
    }

    // Punto del cliente (llega desde afuera, por ejemplo con "Usar mi ubicación")
    if (this.latitud !== null && this.longitud !== null) {
      const actual = this.clienteMarker?.getLatLng();
      const yaEstaAhi = actual !== undefined &&
        Math.abs(actual.lat - this.latitud) < 1e-7 &&
        Math.abs(actual.lng - this.longitud) < 1e-7;
      if (!yaEstaAhi) {
        this.colocarCliente(this.latitud, this.longitud, false);
        this.map.setView([this.latitud, this.longitud], Math.max(this.map.getZoom(), 15));
      }
    }
  }

  private colocarCliente(lat: number, lng: number, emitir: boolean): void {
    if (!this.map) {
      return;
    }
    if (!this.clienteMarker) {
      this.clienteMarker = L.marker([lat, lng], {
        draggable: true,
        icon: this.icono('#0f3460')
      }).addTo(this.map);
      this.clienteMarker.bindTooltip('Tu ubicación de entrega');
      this.clienteMarker.on('dragend', () => {
        const p = this.clienteMarker!.getLatLng();
        this.emitirPunto(p.lat, p.lng);
      });
    } else {
      this.clienteMarker.setLatLng([lat, lng]);
    }
    if (emitir) {
      this.emitirPunto(lat, lng);
    }
  }

  private emitirPunto(lat: number, lng: number): void {
    this.zone.run(() => this.ubicacionChange.emit({ lat, lng }));
  }

  // Punto de color hecho con HTML, para no depender de imágenes de Leaflet.
  private icono(color: string): L.DivIcon {
    return L.divIcon({
      className: '',
      html: `<div style="width:22px;height:22px;border-radius:50%;background:${color};border:3px solid #fff;box-shadow:0 1px 6px rgba(0,0,0,.5)"></div>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });
  }
}