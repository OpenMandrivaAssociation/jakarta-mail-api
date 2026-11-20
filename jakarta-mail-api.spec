Name:		jakarta-mail-api
Version:	2.1.5
Release:	1
Summary:	Jakarta Mail API
Group:		Development/Java
License:	EPL-2.0 OR GPL-2.0-only WITH Classpath-exception-2.0
URL:		https://github.com/jakartaee/mail-api
Source0:	https://github.com/jakartaee/mail-api/archive/refs/tags/%{version}.tar.gz#/jakarta-mail-api-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(jakarta.activation:jakarta.activation-api)

%description
Jakarta Mail API 2.1.5, coordinate jakarta.mail:jakarta.mail-api.
JavaMail 1.6.2 stays java.mail.jar. This jar is jakarta.mail and does
not replace it. Angus Mail is the implementation.

%prep
%autosetup -n mail-api-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete
python - << 'PY'
from pathlib import Path
files = [path for path in Path("api/src/main/java").rglob("*.java") if path.name != "module-info.java"]
if len(files) != 112:
    raise SystemExit("api sources " + str(len(files)))
PY

%build
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p classes generated/jakarta/mail
python - << 'PY'
from pathlib import Path
src = Path("api/src/main/resources/jakarta/mail/Version.java")
text = src.read_text(encoding="utf-8").replace("${mail.version}", "%{version}")
if "${mail.version}" in text:
    raise SystemExit("Version.java was not filtered")
Path("generated/jakarta/mail/Version.java").write_text(text, encoding="utf-8")
PY
find api/src/main/java -name '*.java' ! -name module-info.java > sources.list
echo generated/jakarta/mail/Version.java >> sources.list
test "$(wc -l < sources.list)" -eq 113
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp %{_javadir}/jakarta.activation-api.jar \
	-d classes @sources.list
jar cf jakarta.mail-api.jar -C classes .
jar tf jakarta.mail-api.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
javap -verbose -cp jakarta.mail-api.jar jakarta.mail.Version | grep -F 'major version: 52'
javap -verbose -p -cp jakarta.mail-api.jar jakarta.mail.Version | grep -F 'String %{version}'

python - << 'PY'
text = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>jakarta.mail</groupId>
  <artifactId>jakarta.mail-api</artifactId>
  <version>%{version}</version>
  <name>Jakarta Mail API</name>
  <description>Jakarta Mail API %{version}.</description>
  <url>https://github.com/jakartaee/mail-api</url>
  <licenses>
    <license>
      <name>EPL-2.0 OR GPL-2.0-only WITH Classpath-exception-2.0</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>jakarta.activation</groupId>
      <artifactId>jakarta.activation-api</artifactId>
      <version>2.1.4</version>
    </dependency>
  </dependencies>
</project>
"""
open("jakarta.mail-api.pom", "w", encoding="utf-8").write(text)
PY

%install
sysjar install --buildroot %{buildroot} \
	--artifact jakarta.mail-api.pom:jakarta.mail-api.jar \
	--file-name jakarta.mail-api \
	--filelist .mfiles

%check
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/jakarta.mail-api.jar
test -f "$JAR"
mkdir -p check
cat > check/Smoke.java << 'END'
import jakarta.mail.internet.InternetAddress;
import java.lang.reflect.Field;
public class Smoke {
	public static void main(String[] args) throws Exception {
		InternetAddress address = new InternetAddress("mailapi@example.test");
		address.validate();
		Class<?> version = Class.forName("jakarta.mail.Version");
		Field field = version.getDeclaredField("version");
		field.setAccessible(true);
		String found = String.valueOf(field.get(null));
		if (!"%{version}".equals(found) || !"mailapi@example.test".equals(address.getAddress())) {
			throw new AssertionError(found + " " + address.getAddress());
		}
		System.out.println("mailapi_ok " + found + " " + address.getAddress());
	}
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp "$JAR:%{_javadir}/jakarta.activation-api.jar" \
	-d check check/Smoke.java
java -cp "check:$JAR:%{_javadir}/jakarta.activation-api.jar" Smoke > check/out.txt
cat check/out.txt
grep -F -qx 'mailapi_ok %{version} mailapi@example.test' check/out.txt

%files -f .mfiles
%license LICENSE.md
%doc README.md NOTICE.md
