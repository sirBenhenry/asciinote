# Maintainer: Your Name <youremail@domain.com>
pkgname=asciicanvas
pkgver=0.1.0
pkgrel=1
pkgdesc="An infinite 2D monospaced canvas editor."
arch=('any')
url="https://github.com/your-repo/asciicanvas"
license=('MIT')
depends=('python' 'python-pyside6' 'python-msgpack' 'python-zstandard' 'python-reportlab')
makedepends=('python-setuptools')
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py install --root="$pkgdir/" --optimize=1
}
