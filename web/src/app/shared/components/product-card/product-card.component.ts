import { Component, Input } from '@angular/core';
import { Product } from '../../../core/models/product.interface';

@Component({
  selector: 'app-product-card',
  templateUrl: './product-card.component.html',
  styleUrls: ['./product-card.component.scss']
})
export class ProductCardComponent {
  @Input() product!: Product;

  getPriceRange(): string {
    if (!this.product.variantes || this.product.variantes.length === 0) {
      return 'Sin precio';
    }
    const prices = this.product.variantes.map(v => Number(v.precio));
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    return min === max ? `Bs ${min.toFixed(2)}` : `Bs ${min.toFixed(2)} - Bs ${max.toFixed(2)}`;
  }
}