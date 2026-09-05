import { Pipe, PipeTransform } from '@angular/core';


@Pipe({
  name: 'dateFormat'
})
export class DateFormatPipe implements PipeTransform {


  transform(value: string | Date | null | undefined): string {

    if (!value) {

      return '';

    }


    const date = new Date(value);


    return date.toLocaleDateString(
      'es-BO',
      {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      }
    );

  }

}