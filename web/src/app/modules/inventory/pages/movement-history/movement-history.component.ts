import { Component, OnInit } from '@angular/core';
import { InventoryService } from '../../services/inventory.service';
import { InventoryMovement } from '../../../../core/models/inventory.interface';

@Component({
  selector: 'app-movement-history',
  templateUrl: './movement-history.component.html',
  styleUrls: ['./movement-history.component.scss']
})
export class MovementHistoryComponent implements OnInit {
  movements: InventoryMovement[] = [];
  loading = false;

  constructor(private inventoryService: InventoryService) {}

  ngOnInit(): void {
    this.loadMovements();
  }

  loadMovements(): void {
    this.loading = true;
    this.inventoryService.getMovements().subscribe({
      next: (data: any) => {
        this.movements = data.results || data;
        this.loading = false;
      },
      error: () => {
        this.movements = [];
        this.loading = false;
      }
    });
  }
}