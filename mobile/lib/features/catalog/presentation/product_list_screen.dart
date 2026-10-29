// mobile/lib/features/catalog/presentation/product_list_screen.dart
//
// MODIFICADO (SaaS - 6.2): catálogo consultable sin conexión.
// - Con conexión y sin filtros se descargan todos los productos y se
//   actualiza la copia local (productos_local / variantes_producto_local).
// - Sin conexión se muestra la copia local, con búsqueda y filtros locales,
//   y se avisa la fecha de la copia (puede estar desactualizada).
// Del modelo solo se importa Product: sus clases Color/Size chocan con las de Flutter.
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/models/product_model.dart' show Product;
import '../../../core/network/api_client.dart';
import '../../../core/offline/conexion.dart';
import '../../../core/services/auth_service.dart';
import '../../../shared/widgets/loading_overlay.dart';
import '../../../shared/widgets/product_card.dart';
import '../../../shared/widgets/empty_state.dart';
import '../../reservations/data/reserva_offline_service.dart';
import '../data/repositories/catalog_repository_impl.dart';
import '../data/sources/catalog_remote_source.dart';
import 'product_detail_screen.dart';
import '../../cart_checkout/presentation/cart_screen.dart';

class ProductListScreen extends StatefulWidget {
  const ProductListScreen({super.key});
  @override
  State<ProductListScreen> createState() => _ProductListScreenState();
}

class _ProductListScreenState extends State<ProductListScreen> {
  late final CatalogRepositoryImpl _catalogRepository;
  late final ReservaOfflineService _offline;
  List<Product> _products = [];
  List<dynamic> _categories = [];
  List<dynamic> _brands = [];
  List<dynamic> _sizes = [];
  List<dynamic> _colors = [];
  bool _isLoading = false;
  String? _selectedCategory;
  String? _selectedBrand;
  String? _selectedSize;
  String? _selectedColor;
  String _searchQuery = '';
  // NUEVO (6.2): la lista sale de la copia guardada en el teléfono.
  bool _usandoCopia = false;
  DateTime? _fechaCopia;

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _catalogRepository = CatalogRepositoryImpl(
      remoteSource: CatalogRemoteSource(apiClient: apiClient),
    );
    _offline = context.read<ReservaOfflineService>();
    _loadFilters();
    _loadProducts();
  }

  bool get _sinFiltros =>
      _selectedCategory == null &&
      _selectedBrand == null &&
      _selectedSize == null &&
      _selectedColor == null &&
      _searchQuery.trim().isEmpty;

  Future<void> _loadFilters() async {
    try {
      final categories = await _catalogRepository.getCategories();
      final brands = await _catalogRepository.getBrands();
      final sizes = await _catalogRepository.getSizes();
      final colors = await _catalogRepository.getColors();
      if (mounted) {
        setState(() {
          _categories = categories;
          _brands = brands;
          _sizes = sizes;
          _colors = colors;
        });
      }
    } catch (e) {
      // Sin conexión: los filtros salen de los productos guardados.
      if (esErrorDeRed(e)) await _filtrosDesdeCopia();
    }
  }

  Future<void> _filtrosDesdeCopia() async {
    final locales = await _offline.productosLocales();
    final categorias = <String>{};
    final marcas = <String>{};
    final tallas = <String>{};
    final colores = <String>{};
    for (final p in locales) {
      if (p['categoria'] is Map) categorias.add('${p['categoria']['nombre']}');
      if (p['marca'] is Map) marcas.add('${p['marca']['nombre']}');
      for (final v in (p['variantes'] as List? ?? [])) {
        if (v['talla'] is Map) tallas.add('${v['talla']['nombre']}');
        if (v['color'] is Map) colores.add('${v['color']['nombre']}');
      }
    }
    List<dynamic> lista(Set<String> nombres) =>
        (nombres.toList()..sort()).map((n) => {'nombre': n}).toList();
    if (!mounted) return;
    setState(() {
      _categories = lista(categorias);
      _brands = lista(marcas);
      _sizes = lista(tallas);
      _colors = lista(colores);
    });
  }

  Future<void> _loadProducts() async {
    setState(() {
      _isLoading = true;
    });
    if (_offline.enLinea) {
      try {
        List<Product> productos;
        if (_sinFiltros) {
          // Lista completa: se aprovecha para renovar la copia local.
          final json = await _offline.descargarProductos();
          productos = json.map((p) => Product.fromJson(p)).toList();
        } else {
          final entidades = await _catalogRepository.getProducts(
            categoria: _selectedCategory,
            marca: _selectedBrand,
            talla: _selectedSize,
            color: _selectedColor,
            busqueda: _searchQuery,
          );
          productos = entidades.map((entity) => entity.toModel()).toList();
        }
        if (mounted) {
          setState(() {
            _products = productos;
            _usandoCopia = false;
            _isLoading = false;
          });
        }
        return;
      } catch (e) {
        if (!esErrorDeRed(e)) {
          if (mounted) {
            setState(() {
              _products = [];
              _isLoading = false;
            });
          }
          return;
        }
        _offline.marcarSinConexion();
      }
    }
    await _cargarDesdeCopia();
  }

  Future<void> _cargarDesdeCopia() async {
    final locales = await _offline.productosLocales();
    final filtrados = locales.where(_cumpleFiltros).map((p) => Product.fromJson(p)).toList();
    if (!mounted) return;
    setState(() {
      _products = filtrados;
      _usandoCopia = true;
      _fechaCopia = _offline.fechaCatalogo;
      _isLoading = false;
    });
  }

  /// Filtros y búsqueda aplicados a la copia local (sin importar tildes).
  bool _cumpleFiltros(Map<String, dynamic> p) {
    final variantes = (p['variantes'] as List? ?? []);
    if (_selectedCategory != null &&
        !(p['categoria'] is Map && p['categoria']['nombre'] == _selectedCategory)) {
      return false;
    }
    if (_selectedBrand != null &&
        !(p['marca'] is Map && p['marca']['nombre'] == _selectedBrand)) {
      return false;
    }
    if (_selectedSize != null &&
        !variantes.any((v) => v['talla'] is Map && v['talla']['nombre'] == _selectedSize)) {
      return false;
    }
    if (_selectedColor != null &&
        !variantes.any((v) => v['color'] is Map && v['color']['nombre'] == _selectedColor)) {
      return false;
    }
    final buscado = _normalizar(_searchQuery.trim());
    if (buscado.isNotEmpty) {
      final texto = _normalizar('${p['nombre']} ${p['empresa_nombre'] ?? ''}');
      final codigos = variantes.map((v) => _normalizar('${v['codigo_producto'] ?? ''}'));
      if (!texto.contains(buscado) && !codigos.any((c) => c.contains(buscado))) return false;
    }
    return true;
  }

  String _normalizar(String texto) {
    const conTilde = 'áàäâéèëêíìïîóòöôúùüûñ';
    const sinTilde = 'aaaaeeeeiiiioooouuuun';
    final buffer = StringBuffer();
    for (final rune in texto.toLowerCase().runes) {
      final c = String.fromCharCode(rune);
      final i = conTilde.indexOf(c);
      buffer.write(i >= 0 ? sinTilde[i] : c);
    }
    return buffer.toString();
  }

  void _showFilterSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(24),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Filtros',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String?>(
                value: _selectedCategory,
                decoration: const InputDecoration(labelText: 'Categoría'),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Todas'),
                  ),
                  ..._categories.map<DropdownMenuItem<String?>>((cat) {
                    return DropdownMenuItem<String?>(
                      value: cat['nombre'],
                      child: Text(cat['nombre']),
                    );
                  }),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedCategory = value;
                  });
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                value: _selectedBrand,
                decoration: const InputDecoration(labelText: 'Marca'),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Todas'),
                  ),
                  ..._brands.map<DropdownMenuItem<String?>>((brand) {
                    return DropdownMenuItem<String?>(
                      value: brand['nombre'],
                      child: Text(brand['nombre']),
                    );
                  }),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedBrand = value;
                  });
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                value: _selectedSize,
                decoration: const InputDecoration(labelText: 'Talla'),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Todas'),
                  ),
                  ..._sizes.map<DropdownMenuItem<String?>>((size) {
                    return DropdownMenuItem<String?>(
                      value: size['nombre'],
                      child: Text(size['nombre']),
                    );
                  }),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedSize = value;
                  });
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                value: _selectedColor,
                decoration: const InputDecoration(labelText: 'Color'),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Todos'),
                  ),
                  ..._colors.map<DropdownMenuItem<String?>>((color) {
                    return DropdownMenuItem<String?>(
                      value: color['nombre'],
                      child: Text(color['nombre']),
                    );
                  }),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedColor = value;
                  });
                },
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        setState(() {
                          _selectedCategory = null;
                          _selectedBrand = null;
                          _selectedSize = null;
                          _selectedColor = null;
                        });
                        Navigator.pop(context);
                        _loadProducts();
                      },
                      child: const Text('Limpiar'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () {
                        Navigator.pop(context);
                        _loadProducts();
                      },
                      child: const Text('Aplicar'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _handleLogout() async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cerrar sesión'),
        content: const Text('¿Seguro que quieres cerrar sesión?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
    if (confirmar == true && mounted) {
      await context.read<AuthService>().logout();
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(
          context,
          '/login',
          (route) => false,
        );
      }
    }
  }

  Widget _avisoSinConexion() {
    final fecha = _fechaCopia;
    final texto = fecha != null
        ? 'Sin conexión: estás viendo información guardada en este dispositivo el '
            '${DateFormat('dd/MM/yyyy HH:mm').format(fecha.toLocal())}. '
            'Precios y disponibilidad pueden estar desactualizados.'
        : 'Sin conexión: puedes consultar lo que ya se descargó y registrar ventas o reservas; '
            'se enviarán al recuperar internet.';
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF3E0),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(texto, style: const TextStyle(fontSize: 12, color: Color(0xFF8A4B00))),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SmartLook'),
        actions: [
          IconButton(
            icon: const Icon(Icons.shopping_cart_outlined),
            tooltip: 'Carrito',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const CartScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterSheet,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: _handleLogout,
          ),
        ],
      ),
      body: LoadingOverlay(
        isLoading: _isLoading,
        message: 'Cargando productos...',
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                decoration: InputDecoration(
                  hintText: 'Buscar producto...',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _searchQuery.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            setState(() {
                              _searchQuery = '';
                            });
                            _loadProducts();
                          },
                        )
                      : null,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onChanged: (value) {
                  setState(() {
                    _searchQuery = value;
                  });
                },
                onSubmitted: (_) => _loadProducts(),
              ),
            ),
            if (_usandoCopia) _avisoSinConexion(),
            Expanded(
              child: RefreshIndicator(
                onRefresh: _loadProducts,
                child: _products.isEmpty && !_isLoading
                    ? ListView(
                        physics: const AlwaysScrollableScrollPhysics(),
                        children: const [
                          SizedBox(height: 60),
                          EmptyState(
                            icon: Icons.shopping_bag,
                            title: 'No hay productos',
                            subtitle: 'No se encontraron productos con los filtros seleccionados',
                          ),
                        ],
                      )
                    : GridView.builder(
                        physics: const AlwaysScrollableScrollPhysics(),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2,
                          childAspectRatio: 0.65,
                          crossAxisSpacing: 12,
                          mainAxisSpacing: 12,
                        ),
                        itemCount: _products.length,
                        itemBuilder: (context, index) {
                          final product = _products[index];
                          return ProductCard(
                            product: product,
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => ProductDetailScreen(
                                    productId: product.idProducto,
                                  ),
                                ),
                              );
                            },
                          );
                        },
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}